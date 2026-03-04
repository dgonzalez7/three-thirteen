import pytest
import random

from game.engine import (
    build_deck, init_game, draw_from_pile, draw_from_discard,
    discard_card, attempt_go_out, score_hand, advance_to_next_round,
)
from game.state import (
    Card, Suit, Rank, GamePhase, TurnPhase,
    ROUND_WILD, RANK_POINTS, decks_for_players, LobbyPlayer,
)

from tests.test_engine import make_lobby_players, card


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _expected_card_count(n_players: int, round_number: int) -> int:
    """Total cards that should exist across all hands + draw pile + discard pile."""
    n_decks = decks_for_players(n_players)
    return n_decks * 52


def _all_cards_in_play(gs) -> list:
    """Collect every card visible in the current game state."""
    cards = []
    for p in gs.players:
        cards.extend(p.hand)
    cards.extend(gs.draw_pile)
    cards.extend(gs.discard_pile)
    return cards


def _assert_invariants(gs, context: str = "") -> None:
    """Assert structural invariants that must hold after every action."""
    tag = f" [{context}]" if context else ""

    # Phase and turn-phase are valid enum values
    assert gs.phase in list(GamePhase), f"Invalid phase {gs.phase!r}{tag}"
    assert gs.turn_phase in list(TurnPhase), f"Invalid turn_phase {gs.turn_phase!r}{tag}"

    n = len(gs.players)
    assert n > 0, f"No players{tag}"
    assert 0 <= gs.current_player_index < n, (
        f"current_player_index {gs.current_player_index} out of bounds (n={n}){tag}"
    )

    # Each player's hand has no duplicate card IDs
    for p in gs.players:
        ids = [c.id for c in p.hand]
        assert len(ids) == len(set(ids)), (
            f"Duplicate card IDs in {p.name}'s hand: {ids}{tag}"
        )

    # Card conservation: total cards in play equals deck size
    all_cards = _all_cards_in_play(gs)
    expected = _expected_card_count(n, gs.round_number)
    assert len(all_cards) == expected, (
        f"Card conservation violated: {len(all_cards)} != {expected}{tag}"
    )


def _assert_round_end_invariants(gs, context: str = "") -> None:
    """Assert invariants that must hold when the round reaches SCORING phase."""
    tag = f" [{context}]" if context else ""

    assert gs.phase == GamePhase.SCORING, f"Expected SCORING phase{tag}"

    # At least one player must have triggered go-out
    gone_out = [p for p in gs.players if p.has_gone_out]
    assert len(gone_out) >= 1, (
        f"Expected at least 1 player to have gone out, got 0{tag}"
    )

    # The initiating go-out player (gone_out_player_id) must have round_score == 0
    assert gs.gone_out_player_id is not None, f"gone_out_player_id is None{tag}"
    initiator = next(p for p in gs.players if p.id == gs.gone_out_player_id)
    assert initiator.round_score == 0, (
        f"Initiating go-out player {initiator.name} should have round_score=0, "
        f"got {initiator.round_score}{tag}"
    )

    # All players who went out must have round_score == 0
    for p in gone_out:
        assert p.round_score == 0, (
            f"Player {p.name} has has_gone_out=True but round_score={p.round_score}{tag}"
        )

    # Players who did NOT go out: round_score must match score_hand
    for p in gs.players:
        if not p.has_gone_out:
            expected_score = score_hand(p.hand, gs.wild_rank)
            assert p.round_score == expected_score, (
                f"Player {p.name} round_score={p.round_score} but "
                f"score_hand={expected_score}{tag}"
            )

    assert len(gs.last_round_results) == len(gs.players), (
        f"last_round_results has {len(gs.last_round_results)} entries "
        f"but expected {len(gs.players)}{tag}"
    )


def _bot_take_turn(gs, rng: random.Random):
    """Execute one bot turn: draw, optionally go out, otherwise discard randomly.

    Returns the updated gs. Asserts no engine function returns an error.
    """
    player = gs.players[gs.current_player_index]

    late_game = gs.round_number >= 8

    # --- Draw phase ---
    if gs.turn_phase == TurnPhase.DRAW:
        use_discard = False
        if gs.discard_pile:
            discard_top = gs.discard_pile[-1]
            if late_game:
                # Heuristic: take discard if its rank matches any card already in hand
                hand_ranks = {c.rank for c in player.hand}
                use_discard = discard_top.rank in hand_ranks
            else:
                current_score = score_hand(player.hand, gs.wild_rank)
                candidate_hand = player.hand + [discard_top]
                worst = max(candidate_hand, key=lambda c: score_hand([x for x in candidate_hand if x is not c], gs.wild_rank))
                new_score = score_hand([x for x in candidate_hand if x is not worst], gs.wild_rank)
                use_discard = new_score < current_score
        if not use_discard and not gs.draw_pile:
            use_discard = True
        if use_discard:
            gs, err = draw_from_discard(gs, player.id)
        else:
            gs, err = draw_from_pile(gs, player.id)
        assert err is None, f"Draw error for {player.name}: {err}"
        _assert_invariants(gs, f"after draw by {player.name} r{gs.round_number}")

    # --- Discard phase ---
    player = gs.players[gs.current_player_index]
    assert gs.turn_phase == TurnPhase.DISCARD, (
        f"Expected DISCARD turn_phase after draw, got {gs.turn_phase}"
    )

    if late_game:
        # Heuristic: discard highest RANK_POINTS card that is not wild and not in a pair
        hand_rank_counts = {}
        for c in player.hand:
            hand_rank_counts[c.rank] = hand_rank_counts.get(c.rank, 0) + 1
        non_pair_non_wild = [
            c for c in player.hand
            if c.rank != gs.wild_rank and hand_rank_counts[c.rank] < 2
        ]
        candidates = non_pair_non_wild if non_pair_non_wild else list(player.hand)
        best_card = max(candidates, key=lambda c: RANK_POINTS.get(c.rank, 0))
    else:
        best_card = min(
            player.hand,
            key=lambda c: score_hand([x for x in player.hand if x is not c], gs.wild_rank),
        )

    remaining_after_best = [x for x in player.hand if x is not best_card]

    if score_hand(remaining_after_best, gs.wild_rank) == 0:
        gs, err = attempt_go_out(gs, player.id, best_card.id)
        assert err is None, f"go_out error for {player.name}: {err}"
        _assert_invariants(gs, f"after go_out by {player.name} r{gs.round_number}")
    else:
        gs, err = discard_card(gs, player.id, best_card.id)
        assert err is None, f"Discard error for {player.name}: {err}"
        _assert_invariants(gs, f"after discard by {player.name} r{gs.round_number}")

    return gs


def _play_round(gs, rng: random.Random, n_players: int = 0, game_num: int = 0) -> tuple:
    """Play one full round to SCORING. Returns (gs, per_player_round_scores dict)."""
    max_turns = 500
    turns = 0
    while gs.phase in (GamePhase.PLAYING, GamePhase.FINAL_TURNS):
        if turns >= max_turns:
            pytest.fail(
                f"Round did not complete within {max_turns} turns — possible infinite loop "
                f"(players={n_players}, game={game_num}, round={gs.round_number})"
            )
        if turns > 0 and turns % 50 == 0:
            print(
                f"[sim] players={n_players} game={game_num} round={gs.round_number} turn={turns}",
                flush=True,
            )
        gs = _bot_take_turn(gs, rng)
        turns += 1

    _assert_round_end_invariants(gs, f"round {gs.round_number} end")

    # Snapshot round scores before advancing
    round_scores = {p.id: p.round_score for p in gs.players}
    return gs, round_scores


def _simulate_full_game(n_players: int, seed: int, game_num: int = 0) -> None:
    """Run a complete 11-round game and assert all invariants."""
    rng = random.Random(seed)
    lp = make_lobby_players(n_players)
    gs = init_game("room-sim", lp, rng=rng)

    _assert_invariants(gs, "after init_game")

    cumulative = {p.id: 0 for p in gs.players}

    for round_num in range(1, 12):
        print(f"[sim] players={n_players} game={game_num} round={round_num}", flush=True)

        assert gs.round_number == round_num, (
            f"Expected round {round_num}, got {gs.round_number}"
        )

        gs, round_scores = _play_round(gs, rng, n_players=n_players, game_num=game_num)

        # Accumulate scores manually for final verification
        for pid, score in round_scores.items():
            cumulative[pid] += score

        if round_num < 11:
            # Simulate all players confirming next round
            for p in gs.players:
                gs.next_round_confirmed_by.append(p.id)
            gs = advance_to_next_round(gs, rng=rng)
            _assert_invariants(gs, f"after advance to round {round_num + 1}")
        else:
            # Last round: advance triggers FINISHED
            for p in gs.players:
                gs.next_round_confirmed_by.append(p.id)
            gs = advance_to_next_round(gs, rng=rng)

    assert gs.phase == GamePhase.FINISHED, (
        f"Expected FINISHED after 11 rounds, got {gs.phase}"
    )

    # Cumulative scores must match what we tracked manually
    for p in gs.players:
        assert p.cumulative_score == cumulative[p.id], (
            f"Player {p.name} cumulative_score={p.cumulative_score} "
            f"but manually tracked {cumulative[p.id]}"
        )

    # Winner must have the lowest cumulative score
    min_score = min(p.cumulative_score for p in gs.players)
    winner = next(p for p in gs.players if p.cumulative_score == min_score)
    assert winner.cumulative_score <= min(
        p.cumulative_score for p in gs.players
    ), "Winner determination inconsistent"


# ---------------------------------------------------------------------------
# Parameterized simulation tests
# ---------------------------------------------------------------------------

_PLAYER_COUNTS = [2, 3, 4, 5]
_GAMES_PER_COUNT = 10

_params = [
    pytest.param(n_players, game_num, id=f"p{n_players}_g{game_num:02d}")
    for n_players in _PLAYER_COUNTS
    for game_num in range(1, _GAMES_PER_COUNT + 1)
]


class TestFullGameSimulation:
    @pytest.mark.parametrize("n_players,game_num", _params)
    def test_full_game(self, n_players: int, game_num: int) -> None:
        """Simulate a complete 11-round game and verify all invariants."""
        seed = game_num * 100 + n_players
        _simulate_full_game(n_players, seed, game_num=game_num)
