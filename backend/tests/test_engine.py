import pytest
import random

from game.engine import (
    build_deck, init_game, draw_from_pile, draw_from_discard,
    discard_card, attempt_go_out, score_hand, compute_round_results,
    advance_to_next_round,
)
from game.state import (
    Card, Suit, Rank, GamePhase, TurnPhase,
    ROUND_WILD, RANK_POINTS, decks_for_players, LobbyPlayer,
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def make_lobby_players(n: int):
    return [LobbyPlayer(id=f"p{i}", name=f"Player{i}") for i in range(1, n + 1)]


def seeded_game(n_players: int = 2, round_number: int = 1):
    """Return a deterministic GameState using a fixed RNG seed."""
    lp = make_lobby_players(n_players)
    return init_game("room-1", lp, rng=random.Random(42))


def card(rank: Rank, suit: Suit, deck_idx: int = 0, is_wild: bool = False) -> Card:
    return Card(id=f"{rank.value}_{suit.value}_{deck_idx}", suit=suit, rank=rank, is_wild=is_wild)


# ---------------------------------------------------------------------------
# build_deck
# ---------------------------------------------------------------------------

class TestBuildDeck:
    def test_single_deck_52_cards(self):
        deck = build_deck(2, 1)
        assert len(deck) == 52

    def test_double_deck_104_cards(self):
        deck = build_deck(4, 1)
        assert len(deck) == 104

    def test_triple_deck_156_cards(self):
        deck = build_deck(6, 1)
        assert len(deck) == 156

    def test_wild_flags_set_correctly_round_1(self):
        deck = build_deck(2, 1)
        for c in deck:
            assert c.is_wild == (c.rank == Rank.THREE)

    def test_wild_flags_set_correctly_round_11(self):
        deck = build_deck(2, 11)
        for c in deck:
            assert c.is_wild == (c.rank == Rank.KING)

    def test_all_suits_and_ranks_present(self):
        deck = build_deck(2, 1)
        for suit in Suit:
            for rank in Rank:
                assert any(c.suit == suit and c.rank == rank for c in deck)

    def test_deck_is_shuffled(self):
        d1 = build_deck(2, 1, rng=random.Random(1))
        d2 = build_deck(2, 1, rng=random.Random(2))
        assert [c.id for c in d1] != [c.id for c in d2]

    def test_card_ids_unique_within_single_deck(self):
        deck = build_deck(2, 1)
        ids = [c.id for c in deck]
        assert len(ids) == len(set(ids))


# ---------------------------------------------------------------------------
# init_game / deal
# ---------------------------------------------------------------------------

class TestInitGame:
    def test_correct_player_count(self):
        gs = seeded_game(3)
        assert len(gs.players) == 3

    def test_round_1_deals_3_cards(self):
        gs = seeded_game(2)
        for p in gs.players:
            assert len(p.hand) == 3

    def test_round_5_deals_7_cards(self):
        lp = make_lobby_players(2)
        gs = init_game("room-1", lp, rng=random.Random(0))
        gs.round_number = 5
        from game.engine import _deal_round
        gs = _deal_round(gs)
        for p in gs.players:
            assert len(p.hand) == 7

    def test_discard_pile_has_one_card(self):
        gs = seeded_game(2)
        assert len(gs.discard_pile) == 1

    def test_draw_pile_not_empty(self):
        gs = seeded_game(2)
        assert len(gs.draw_pile) > 0

    def test_phase_is_playing(self):
        gs = seeded_game(2)
        assert gs.phase == GamePhase.PLAYING

    def test_turn_phase_is_draw(self):
        gs = seeded_game(2)
        assert gs.turn_phase == TurnPhase.DRAW

    def test_wild_rank_correct_round_1(self):
        gs = seeded_game(2)
        assert gs.wild_rank == Rank.THREE

    def test_current_player_is_left_of_dealer(self):
        gs = seeded_game(2)
        assert gs.current_player_index == (gs.dealer_index + 1) % 2


# ---------------------------------------------------------------------------
# draw_from_pile
# ---------------------------------------------------------------------------

class TestDrawFromPile:
    def test_draw_adds_card_to_hand(self):
        gs = seeded_game(2)
        pid = gs.players[gs.current_player_index].id
        hand_before = len(gs.players[gs.current_player_index].hand)
        gs, err = draw_from_pile(gs, pid)
        assert err is None
        assert len(gs.players[gs.current_player_index].hand) == hand_before + 1

    def test_draw_removes_card_from_pile(self):
        gs = seeded_game(2)
        pid = gs.players[gs.current_player_index].id
        pile_before = len(gs.draw_pile)
        gs, err = draw_from_pile(gs, pid)
        assert err is None
        assert len(gs.draw_pile) == pile_before - 1

    def test_turn_phase_becomes_discard(self):
        gs = seeded_game(2)
        pid = gs.players[gs.current_player_index].id
        gs, err = draw_from_pile(gs, pid)
        assert gs.turn_phase == TurnPhase.DISCARD

    def test_wrong_player_rejected(self):
        gs = seeded_game(2)
        wrong_pid = gs.players[(gs.current_player_index + 1) % 2].id
        _, err = draw_from_pile(gs, wrong_pid)
        assert err is not None

    def test_draw_twice_rejected(self):
        gs = seeded_game(2)
        pid = gs.players[gs.current_player_index].id
        gs, _ = draw_from_pile(gs, pid)
        _, err = draw_from_pile(gs, pid)
        assert err is not None


# ---------------------------------------------------------------------------
# draw_from_discard
# ---------------------------------------------------------------------------

class TestDrawFromDiscard:
    def test_draw_discard_adds_correct_card(self):
        gs = seeded_game(2)
        pid = gs.players[gs.current_player_index].id
        top_card = gs.discard_pile[-1]
        gs, err = draw_from_discard(gs, pid)
        assert err is None
        assert top_card in gs.players[gs.current_player_index].hand

    def test_draw_discard_removes_from_discard_pile(self):
        gs = seeded_game(2)
        pid = gs.players[gs.current_player_index].id
        pile_before = len(gs.discard_pile)
        gs, err = draw_from_discard(gs, pid)
        assert err is None
        assert len(gs.discard_pile) == pile_before - 1


# ---------------------------------------------------------------------------
# discard_card
# ---------------------------------------------------------------------------

class TestDiscardCard:
    def _draw_then_get(self, gs):
        pid = gs.players[gs.current_player_index].id
        gs, _ = draw_from_pile(gs, pid)
        return gs, pid

    def test_discard_removes_from_hand(self):
        gs = seeded_game(2)
        gs, pid = self._draw_then_get(gs)
        player = gs.players[gs.current_player_index]
        card_id = player.hand[0].id
        gs, err = discard_card(gs, pid, card_id)
        assert err is None
        assert not any(c.id == card_id for p in gs.players for c in p.hand if p.id == pid)

    def test_discard_adds_to_discard_pile(self):
        gs = seeded_game(2)
        gs, pid = self._draw_then_get(gs)
        player = gs.players[gs.current_player_index]
        card_id = player.hand[0].id
        pile_before = len(gs.discard_pile)
        gs, err = discard_card(gs, pid, card_id)
        assert err is None
        assert len(gs.discard_pile) == pile_before + 1

    def test_discard_advances_turn(self):
        gs = seeded_game(2)
        first_idx = gs.current_player_index
        gs, pid = self._draw_then_get(gs)
        card_id = gs.players[gs.current_player_index].hand[0].id
        gs, _ = discard_card(gs, pid, card_id)
        assert gs.current_player_index != first_idx

    def test_discard_wrong_card_id_rejected(self):
        gs = seeded_game(2)
        gs, pid = self._draw_then_get(gs)
        _, err = discard_card(gs, pid, "nonexistent_card_id")
        assert err is not None

    def test_must_draw_before_discard(self):
        gs = seeded_game(2)
        pid = gs.players[gs.current_player_index].id
        card_id = gs.players[gs.current_player_index].hand[0].id
        _, err = discard_card(gs, pid, card_id)
        assert err is not None


# ---------------------------------------------------------------------------
# score_hand
# ---------------------------------------------------------------------------

class TestScoreHand:
    def test_empty_hand_scores_zero(self):
        assert score_hand([], Rank.THREE) == 0

    def test_three_of_a_kind_scores_zero(self):
        hand = [
            card(Rank.SEVEN, Suit.HEARTS),
            card(Rank.SEVEN, Suit.DIAMONDS),
            card(Rank.SEVEN, Suit.CLUBS),
        ]
        assert score_hand(hand, Rank.THREE) == 0

    def test_valid_run_scores_zero(self):
        hand = [
            card(Rank.ACE, Suit.HEARTS),
            card(Rank.TWO, Suit.HEARTS),
            card(Rank.THREE, Suit.HEARTS),
        ]
        # Round wild is THREE so THREE is wild here — still makes a valid run via wild
        assert score_hand(hand, Rank.FOUR) == 0  # wild=4, not in hand

    def test_unmatched_card_scores_face_value(self):
        hand = [card(Rank.KING, Suit.SPADES)]
        assert score_hand(hand, Rank.THREE) == 10

    def test_unmatched_ace_scores_15(self):
        hand = [card(Rank.ACE, Suit.SPADES)]
        assert score_hand(hand, Rank.THREE) == 15

    def test_wild_can_complete_set(self):
        hand = [
            card(Rank.NINE, Suit.HEARTS),
            card(Rank.NINE, Suit.DIAMONDS),
            card(Rank.NINE, Suit.CLUBS, is_wild=True),  # wild=9
        ]
        # The wild substitutes, so the set is valid regardless
        assert score_hand(hand, Rank.NINE) == 0

    def test_pure_run_no_penalty(self):
        hand = [
            card(Rank.FIVE, Suit.CLUBS),
            card(Rank.SIX, Suit.CLUBS),
            card(Rank.SEVEN, Suit.CLUBS),
        ]
        assert score_hand(hand, Rank.THREE) == 0

    def test_mixed_matched_and_unmatched(self):
        hand = [
            card(Rank.FIVE, Suit.CLUBS),
            card(Rank.SIX, Suit.CLUBS),
            card(Rank.SEVEN, Suit.CLUBS),
            card(Rank.KING, Suit.SPADES),
        ]
        assert score_hand(hand, Rank.THREE) == 10  # Only KING is unmatched

    def test_wild_extends_run_at_boundary(self):
        """Round 1: wild=threes. Hand [3♠, 5♥, 6♥] — wild fills 4♥ or 7♥ to
        complete a 3-card run, so total penalty must be 0."""
        hand = [
            card(Rank.THREE, Suit.SPADES),   # wild (rank == wild_rank)
            card(Rank.FIVE, Suit.HEARTS),
            card(Rank.SIX, Suit.HEARTS),
        ]
        assert score_hand(hand, Rank.THREE) == 0

    def test_wild_fills_internal_gap_in_run(self):
        """Wild fills an internal gap: [5♥, 3♠, 7♥] with wild=threes → 5-6-7 run."""
        hand = [
            card(Rank.FIVE, Suit.HEARTS),
            card(Rank.THREE, Suit.SPADES),   # wild fills 6♥
            card(Rank.SEVEN, Suit.HEARTS),
        ]
        assert score_hand(hand, Rank.THREE) == 0

    def test_wild_first_in_hand_order_run(self):
        """Ensure ordering in remaining[] doesn't prevent wild from joining a run
        when the wild card appears before the natural anchor in the list."""
        hand = [
            card(Rank.THREE, Suit.CLUBS),    # wild (appears first)
            card(Rank.NINE, Suit.DIAMONDS),
            card(Rank.TEN, Suit.DIAMONDS),
        ]
        # wild fills 8♦ or J♦ → valid run, penalty = 0
        assert score_hand(hand, Rank.THREE) == 0

    # ------------------------------------------------------------------
    # Set size / composition edge cases
    # ------------------------------------------------------------------

    def test_four_of_a_kind_scores_zero(self):
        hand = [
            card(Rank.SEVEN, Suit.HEARTS),
            card(Rank.SEVEN, Suit.DIAMONDS),
            card(Rank.SEVEN, Suit.CLUBS),
            card(Rank.SEVEN, Suit.SPADES),
        ]
        assert score_hand(hand, Rank.THREE) == 0

    def test_multideck_duplicate_cards_two_sets(self):
        """Multi-deck hand: 3♦ 3♦ 3♥ 3♠ A♦ A♦ 7♦ (wild=7s).
        Should form set-of-four-3s + set-of-three-aces (wild as third ace).
        Both 3♦ copies and both A♦ copies must be treated as distinct cards.
        Penalty = 0.
        """
        hand = [
            card(Rank.THREE, Suit.DIAMONDS, deck_idx=0),
            card(Rank.THREE, Suit.DIAMONDS, deck_idx=1),  # duplicate 3♦
            card(Rank.THREE, Suit.HEARTS),
            card(Rank.THREE, Suit.SPADES),
            card(Rank.ACE, Suit.DIAMONDS, deck_idx=0),
            card(Rank.ACE, Suit.DIAMONDS, deck_idx=1),   # duplicate A♦
            card(Rank.SEVEN, Suit.DIAMONDS),              # wild
        ]
        assert score_hand(hand, Rank.SEVEN) == 0

    def test_multideck_three_sets_three_wilds_canonical_order(self):
        """6♦ 6♠ 9♠ J♥ J♣ 9♣ 3♣ 3♦ 9♣ (wild=9s, two distinct 9♣).
        Valid partition: {6♦,6♠,9♠} + {J♥,J♣,9♣_0} + {3♣,3♦,9♣_1}.
        Penalty = 0.
        """
        hand = [
            card(Rank.SIX,   Suit.DIAMONDS),
            card(Rank.SIX,   Suit.SPADES),
            card(Rank.NINE,  Suit.SPADES),
            card(Rank.JACK,  Suit.HEARTS),
            card(Rank.JACK,  Suit.CLUBS),
            card(Rank.NINE,  Suit.CLUBS, deck_idx=0),
            card(Rank.THREE, Suit.CLUBS),
            card(Rank.THREE, Suit.DIAMONDS),
            card(Rank.NINE,  Suit.CLUBS, deck_idx=1),   # duplicate 9♣
        ]
        assert score_hand(hand, Rank.NINE) == 0

    def test_multideck_three_sets_wild_before_natural_partner(self):
        """Regression for prefix-slicing bug: wild appears before the natural
        same-rank partner in the hand list, causing the set-finder to miss the
        valid combo when using prefix [:size] instead of combinations.

        Hand (wild=9s): [3♦, 9♣_0(wild), 6♠, J♥, J♣, 9♠(wild), 6♦, 9♣_1(wild), 3♣]
        i.e. the wild 9♣_0 is listed BEFORE 3♣ in remaining[] when 3♦ is the anchor.
        _sets_containing(3♦, [...]) must still find {3♦, 3♣, 9*} regardless of order.
        Penalty = 0.
        """
        hand = [
            card(Rank.THREE, Suit.DIAMONDS),              # anchor — same-rank partner 3♣ is last
            card(Rank.NINE,  Suit.CLUBS, deck_idx=0),     # wild comes BEFORE 3♣ in list
            card(Rank.SIX,   Suit.SPADES),
            card(Rank.JACK,  Suit.HEARTS),
            card(Rank.JACK,  Suit.CLUBS),
            card(Rank.NINE,  Suit.SPADES),                # wild
            card(Rank.SIX,   Suit.DIAMONDS),
            card(Rank.NINE,  Suit.CLUBS, deck_idx=1),     # duplicate wild 9♣
            card(Rank.THREE, Suit.CLUBS),                 # natural partner — last in list
        ]
        assert score_hand(hand, Rank.NINE) == 0

    def test_multideck_three_sets_all_orderings_sample(self):
        """Score must be 0 for 1000 random permutations of the 9-card hand."""
        import random as _random
        base = [
            card(Rank.SIX,   Suit.DIAMONDS),
            card(Rank.SIX,   Suit.SPADES),
            card(Rank.NINE,  Suit.SPADES),
            card(Rank.JACK,  Suit.HEARTS),
            card(Rank.JACK,  Suit.CLUBS),
            card(Rank.NINE,  Suit.CLUBS, deck_idx=0),
            card(Rank.THREE, Suit.CLUBS),
            card(Rank.THREE, Suit.DIAMONDS),
            card(Rank.NINE,  Suit.CLUBS, deck_idx=1),
        ]
        rng = _random.Random(0)
        for _ in range(1000):
            perm = list(base)
            rng.shuffle(perm)
            assert score_hand(perm, Rank.NINE) == 0, \
                f"Non-zero score for ordering: {[c.id for c in perm]}"

    def test_wild_first_in_hand_order_set(self):
        """Round 1: wild=threes. Hand [3♣, 6♥, 6♣] — wild fills third 6,
        forming a valid set. Must score 0 regardless of list order."""
        hand = [
            card(Rank.THREE, Suit.CLUBS),   # wild (appears first)
            card(Rank.SIX, Suit.HEARTS),
            card(Rank.SIX, Suit.CLUBS),
        ]
        assert score_hand(hand, Rank.THREE) == 0

    def test_set_with_two_wilds_scores_zero(self):
        """One natural + two wilds = valid three-card set."""
        hand = [
            card(Rank.QUEEN, Suit.HEARTS),
            card(Rank.THREE, Suit.DIAMONDS),  # wild 1
            card(Rank.THREE, Suit.CLUBS),     # wild 2
        ]
        assert score_hand(hand, Rank.THREE) == 0

    def test_set_needs_at_least_three_cards(self):
        """A pair with one wild is exactly 3 cards — valid."""
        hand = [
            card(Rank.JACK, Suit.HEARTS),
            card(Rank.JACK, Suit.SPADES),
            card(Rank.THREE, Suit.CLUBS),  # wild fills third slot
        ]
        assert score_hand(hand, Rank.THREE) == 0

    def test_pair_alone_not_a_set(self):
        """Two non-wild cards of the same rank with no wild = not a valid set."""
        hand = [
            card(Rank.JACK, Suit.HEARTS),
            card(Rank.JACK, Suit.SPADES),
        ]
        assert score_hand(hand, Rank.THREE) == 20  # J=10 each

    def test_two_separate_combinations_score_zero(self):
        """Set of 3 + run of 3 in the same hand — both matched, zero penalty."""
        hand = [
            card(Rank.KING, Suit.HEARTS),
            card(Rank.KING, Suit.DIAMONDS),
            card(Rank.KING, Suit.CLUBS),
            card(Rank.FIVE, Suit.SPADES),
            card(Rank.SIX, Suit.SPADES),
            card(Rank.SEVEN, Suit.SPADES),
        ]
        assert score_hand(hand, Rank.THREE) == 0

    def test_optimal_partition_minimises_penalty(self):
        """When a card could join either of two combinations, the engine must
        choose the assignment that leaves the lowest total penalty.

        Hand: 9♥ 9♦ 9♠ 8♥ 10♥  (wild=four, no wilds present)
        Option A: set {9♥ 9♦ 9♠} — leftover 8♥ 10♥ = 18 pts
        Option B: run {8♥ 9♥ 10♥} — leftover 9♦ 9♠ = 18 pts
        Both options tie at 18; engine must return exactly 18 (not 27 or 36).
        """
        hand = [
            card(Rank.NINE, Suit.HEARTS),
            card(Rank.NINE, Suit.DIAMONDS),
            card(Rank.NINE, Suit.SPADES),
            card(Rank.EIGHT, Suit.HEARTS),
            card(Rank.TEN, Suit.HEARTS),
        ]
        assert score_hand(hand, Rank.FOUR) == 18

    def test_optimal_partition_chooses_lower_penalty_assignment(self):
        """Engine picks the partition that discards a low-value card rather than
        a high-value one when a shared card creates two options.

        Hand: 9♥ 9♦ 9♠  8♥ 10♥  A♠  (wild=four)
        Option A: set {9♥ 9♦ 9♠} + run {8♥ 10♥ ?} — 8-9-10 run needs 9♥, can't
                  reuse it. Leftover: 8♥(8) + 10♥(10) + A♠(15) = 33.
        Option B: run {8♥ 9♥ 10♥} + pair {9♦ 9♠} not a set. Leftover: 9♦+9♠+A♠ = 33.
        Either way = 33.  Add a 9♣ to make the set work alongside the run:
        Hand: 9♥ 9♦ 9♠ 9♣ 8♥ 10♥
        Option A: set-of-4 {9♥9♦9♠9♣} + leftover 8♥(8) + 10♥(10) = 18
        Option B: run {8♥9♥10♥} + set {9♦9♠9♣} + leftover nothing = 0  ← optimal
        """
        hand = [
            card(Rank.NINE, Suit.HEARTS),
            card(Rank.NINE, Suit.DIAMONDS),
            card(Rank.NINE, Suit.SPADES),
            card(Rank.NINE, Suit.CLUBS),
            card(Rank.EIGHT, Suit.HEARTS),
            card(Rank.TEN, Suit.HEARTS),
        ]
        assert score_hand(hand, Rank.FOUR) == 0

    def test_optimal_partition_prefers_lower_penalty(self):
        """A high-value unmatched card should be preferred over a low-value one."""
        # 8♣ 9♣ 10♣ form a run; K♠ is unmatched.
        # Penalty = 10 (K), not 27 (8+9+10).
        hand = [
            card(Rank.EIGHT, Suit.CLUBS),
            card(Rank.NINE, Suit.CLUBS),
            card(Rank.TEN, Suit.CLUBS),
            card(Rank.KING, Suit.SPADES),
        ]
        assert score_hand(hand, Rank.THREE) == 10

    # ------------------------------------------------------------------
    # Run boundary edge cases
    # ------------------------------------------------------------------

    def test_run_at_low_boundary_ace_two_three(self):
        """A-2-3 pure run (Ace is low, no wilds needed)."""
        hand = [
            card(Rank.ACE, Suit.CLUBS),
            card(Rank.TWO, Suit.CLUBS),
            card(Rank.THREE, Suit.CLUBS),
        ]
        # Wild is FOUR — threes are natural here
        assert score_hand(hand, Rank.FOUR) == 0

    def test_run_at_high_boundary_jack_queen_king(self):
        hand = [
            card(Rank.JACK, Suit.HEARTS),
            card(Rank.QUEEN, Suit.HEARTS),
            card(Rank.KING, Suit.HEARTS),
        ]
        assert score_hand(hand, Rank.THREE) == 0

    def test_wild_extends_run_at_high_end(self):
        """Wild appended above Q♦ K♦ (fills A position — but A is low only,
        so wild must fill J♦ below Q or the run extends downward).
        Use J♦ Q♦ + wild filling K♦."""
        hand = [
            card(Rank.JACK, Suit.DIAMONDS),
            card(Rank.QUEEN, Suit.DIAMONDS),
            card(Rank.THREE, Suit.CLUBS),   # wild fills K♦
        ]
        assert score_hand(hand, Rank.THREE) == 0

    def test_wild_extends_run_at_low_end(self):
        """Wild fills Ace below 2♠ 3♠ (wild=four, so 3♠ is natural)."""
        hand = [
            card(Rank.THREE, Suit.SPADES),  # natural (wild=FOUR)
            card(Rank.TWO, Suit.SPADES),
            card(Rank.FOUR, Suit.CLUBS),    # wild fills A♠
        ]
        assert score_hand(hand, Rank.FOUR) == 0

    def test_two_wilds_fill_two_gaps_in_run(self):
        """A run of 5 where two interior positions are filled by wilds."""
        hand = [
            card(Rank.FIVE, Suit.HEARTS),
            card(Rank.THREE, Suit.SPADES),   # wild fills 6♥
            card(Rank.THREE, Suit.CLUBS),    # wild fills 7♥  (deck_idx differs)
            card(Rank.EIGHT, Suit.HEARTS),
            card(Rank.NINE, Suit.HEARTS),
        ]
        # 5-6-7-8-9♥ with two wilds filling 6 and 7 → penalty = 0
        assert score_hand(hand, Rank.THREE) == 0

    def test_run_mixed_suits_not_valid(self):
        """Cards of different suits cannot form a run."""
        hand = [
            card(Rank.FIVE, Suit.HEARTS),
            card(Rank.SIX, Suit.CLUBS),    # different suit
            card(Rank.SEVEN, Suit.HEARTS),
        ]
        # 6♣ breaks the suit — no valid run, all three cards unmatched
        assert score_hand(hand, Rank.FOUR) == 5 + 6 + 7

    def test_run_length_four_natural(self):
        """A four-card run scores zero."""
        hand = [
            card(Rank.TWO, Suit.DIAMONDS),
            card(Rank.THREE, Suit.DIAMONDS),
            card(Rank.FOUR, Suit.DIAMONDS),
            card(Rank.FIVE, Suit.DIAMONDS),
        ]
        assert score_hand(hand, Rank.SEVEN) == 0

    # ------------------------------------------------------------------
    # Wild card edge cases
    # ------------------------------------------------------------------

    def test_all_wilds_form_valid_set(self):
        """Three wild cards together are a valid set (each substitutes freely)."""
        hand = [
            card(Rank.THREE, Suit.HEARTS),
            card(Rank.THREE, Suit.DIAMONDS),
            card(Rank.THREE, Suit.CLUBS),
        ]
        assert score_hand(hand, Rank.THREE) == 0

    def test_single_wild_alone_is_unmatched(self):
        """One wild card by itself has no valid combination — scores its face value."""
        hand = [card(Rank.THREE, Suit.HEARTS)]
        assert score_hand(hand, Rank.THREE) == 3

    def test_wild_not_wasted_on_complete_set(self):
        """Natural four-of-a-kind needs no wild; the wild should remain
        available to help a separate combination."""
        hand = [
            card(Rank.SEVEN, Suit.HEARTS),
            card(Rank.SEVEN, Suit.DIAMONDS),
            card(Rank.SEVEN, Suit.CLUBS),
            card(Rank.SEVEN, Suit.SPADES),
            card(Rank.THREE, Suit.HEARTS),   # wild
            card(Rank.NINE, Suit.CLUBS),
            card(Rank.TEN, Suit.CLUBS),
        ]
        # Wild fills 8♣ → 9-10-wild(8) run; four 7s are a set → all matched
        assert score_hand(hand, Rank.THREE) == 0


# ---------------------------------------------------------------------------
# attempt_go_out
# ---------------------------------------------------------------------------

class TestAttemptGoOut:
    def _setup_going_out(self):
        """Build a game state where current player can go out."""
        gs = seeded_game(2)
        pid = gs.players[gs.current_player_index].id
        player = gs.players[gs.current_player_index]
        # Replace hand with a clean 3-card set + 1 discard card
        player.hand = [
            card(Rank.KING, Suit.HEARTS),
            card(Rank.KING, Suit.DIAMONDS),
            card(Rank.KING, Suit.CLUBS),
            card(Rank.ACE, Suit.SPADES),  # will discard this
        ]
        gs.turn_phase = TurnPhase.DISCARD
        return gs, pid

    def test_valid_go_out_succeeds(self):
        gs, pid = self._setup_going_out()
        discard_id = next(c for c in gs.players[gs.current_player_index].hand if c.rank == Rank.ACE).id
        gs, err = attempt_go_out(gs, pid, discard_id)
        assert err is None
        assert gs.gone_out_player_id == pid

    def test_valid_go_out_phase_becomes_final_turns(self):
        gs, pid = self._setup_going_out()
        discard_id = next(c for c in gs.players[gs.current_player_index].hand if c.rank == Rank.ACE).id
        gs, err = attempt_go_out(gs, pid, discard_id)
        assert gs.phase == GamePhase.FINAL_TURNS

    def test_valid_go_out_sets_final_turns_remaining(self):
        gs, pid = self._setup_going_out()
        n_players = len(gs.players)
        discard_id = next(c for c in gs.players[gs.current_player_index].hand if c.rank == Rank.ACE).id
        gs, _ = attempt_go_out(gs, pid, discard_id)
        assert gs.final_turns_remaining == n_players - 1

    def test_invalid_go_out_rejected(self):
        gs = seeded_game(2)
        pid = gs.players[gs.current_player_index].id
        gs.turn_phase = TurnPhase.DISCARD
        # Hand has no valid combination — cannot go out
        gs.players[gs.current_player_index].hand = [
            card(Rank.ACE, Suit.SPADES),
            card(Rank.KING, Suit.HEARTS),
            card(Rank.TWO, Suit.CLUBS),
            card(Rank.JACK, Suit.DIAMONDS),
        ]
        card_id = gs.players[gs.current_player_index].hand[-1].id
        _, err = attempt_go_out(gs, pid, card_id)
        assert err is not None
        assert "unmatched" in err.lower()

    def test_go_out_rejected_before_drawing(self):
        """Cannot attempt to go out during the draw phase."""
        gs = seeded_game(2)
        pid = gs.players[gs.current_player_index].id
        assert gs.turn_phase == TurnPhase.DRAW
        card_id = gs.players[gs.current_player_index].hand[0].id
        _, err = attempt_go_out(gs, pid, card_id)
        assert err is not None
        assert "draw" in err.lower()

    def test_go_out_rejected_for_wrong_player(self):
        """A player who is not the current player cannot go out."""
        gs = seeded_game(2)
        wrong_idx = (gs.current_player_index + 1) % 2
        wrong_pid = gs.players[wrong_idx].id
        gs.turn_phase = TurnPhase.DISCARD
        card_id = gs.players[wrong_idx].hand[0].id
        _, err = attempt_go_out(gs, wrong_pid, card_id)
        assert err is not None

    def test_go_out_with_card_not_in_hand_rejected(self):
        """Providing a card_id that doesn't exist in the player's hand is rejected."""
        gs = seeded_game(2)
        pid = gs.players[gs.current_player_index].id
        gs.turn_phase = TurnPhase.DISCARD
        _, err = attempt_go_out(gs, pid, "nonexistent_card_id")
        assert err is not None

    def test_go_out_discard_lands_on_discard_pile(self):
        """The discarded card ends up on the top of the discard pile."""
        gs, pid = self._setup_going_out()
        discard_id = next(
            c for c in gs.players[gs.current_player_index].hand
            if c.rank == Rank.ACE
        ).id
        pile_before = len(gs.discard_pile)
        gs, err = attempt_go_out(gs, pid, discard_id)
        assert err is None
        assert len(gs.discard_pile) == pile_before + 1
        assert gs.discard_pile[-1].id == discard_id

    def test_go_out_card_removed_from_hand(self):
        """The discarded card no longer appears in the player's hand."""
        gs, pid = self._setup_going_out()
        discard_id = next(
            c for c in gs.players[gs.current_player_index].hand
            if c.rank == Rank.ACE
        ).id
        gs, err = attempt_go_out(gs, pid, discard_id)
        assert err is None
        gone_out_player = next(p for p in gs.players if p.id == pid)
        assert not any(c.id == discard_id for c in gone_out_player.hand)

    def test_go_out_valid_via_wild(self):
        """A hand that only forms a valid combination with a wild card — should
        be accepted."""
        gs = seeded_game(2)
        pid = gs.players[gs.current_player_index].id
        player = gs.players[gs.current_player_index]
        # Hand: K♥ K♦ 3♠(wild) + A♠ to discard
        # Remaining after discard: K♥ K♦ 3♠ → set-of-kings-with-wild, score=0
        player.hand = [
            card(Rank.KING, Suit.HEARTS),
            card(Rank.KING, Suit.DIAMONDS),
            card(Rank.THREE, Suit.SPADES),  # wild
            card(Rank.ACE, Suit.CLUBS),     # will discard
        ]
        gs.turn_phase = TurnPhase.DISCARD
        discard_id = next(c for c in player.hand if c.rank == Rank.ACE).id
        gs, err = attempt_go_out(gs, pid, discard_id)
        assert err is None
        assert gs.gone_out_player_id == pid

    def test_go_out_valid_with_wild_completing_run(self):
        """Hand uses wild to complete a run for go-out validation."""
        gs = seeded_game(2)
        pid = gs.players[gs.current_player_index].id
        player = gs.players[gs.current_player_index]
        # Remaining after discard: 5♥ 6♥ 3♠(wild) → wild fills 4♥ or 7♥, score=0
        player.hand = [
            card(Rank.FIVE, Suit.HEARTS),
            card(Rank.SIX, Suit.HEARTS),
            card(Rank.THREE, Suit.SPADES),  # wild
            card(Rank.KING, Suit.CLUBS),    # will discard
        ]
        gs.turn_phase = TurnPhase.DISCARD
        discard_id = next(c for c in player.hand if c.rank == Rank.KING).id
        gs, err = attempt_go_out(gs, pid, discard_id)
        assert err is None

    def test_go_out_allowed_during_final_turns(self):
        """A second player may also go out during the final-turns phase (rare but legal)."""
        gs = seeded_game(3)
        # First player goes out
        first_pid = gs.players[gs.current_player_index].id
        player = gs.players[gs.current_player_index]
        player.hand = [
            card(Rank.KING, Suit.HEARTS),
            card(Rank.KING, Suit.DIAMONDS),
            card(Rank.KING, Suit.CLUBS),
            card(Rank.ACE, Suit.SPADES),
        ]
        gs.turn_phase = TurnPhase.DISCARD
        discard_id = next(c for c in player.hand if c.rank == Rank.ACE).id
        gs, err = attempt_go_out(gs, first_pid, discard_id)
        assert err is None
        assert gs.phase == GamePhase.FINAL_TURNS

        # Second player is now current; give them a valid hand and let them go out too
        second_pid = gs.players[gs.current_player_index].id
        second_player = gs.players[gs.current_player_index]
        second_player.hand = [
            card(Rank.QUEEN, Suit.HEARTS),
            card(Rank.QUEEN, Suit.DIAMONDS),
            card(Rank.QUEEN, Suit.CLUBS),
            card(Rank.TWO, Suit.SPADES),
        ]
        gs.turn_phase = TurnPhase.DISCARD
        discard_id2 = next(c for c in second_player.hand if c.rank == Rank.TWO).id
        gs, err2 = attempt_go_out(gs, second_pid, discard_id2)
        assert err2 is None
        assert gs.players[gs.current_player_index].id != first_pid

    def test_gone_out_player_skipped_during_final_turns(self):
        """In a 3-player game the gone-out player must never become current player."""
        gs = seeded_game(3)
        gone_out_idx = gs.current_player_index
        gone_out_pid = gs.players[gone_out_idx].id

        # Force the player into DISCARD phase with a valid hand to go out
        player = gs.players[gone_out_idx]
        player.hand = [
            card(Rank.KING, Suit.HEARTS),
            card(Rank.KING, Suit.DIAMONDS),
            card(Rank.KING, Suit.CLUBS),
            card(Rank.ACE, Suit.SPADES),
        ]
        gs.turn_phase = TurnPhase.DISCARD
        discard_id = next(c for c in player.hand if c.rank == Rank.ACE).id
        gs, err = attempt_go_out(gs, gone_out_pid, discard_id)
        assert err is None
        assert gs.phase == GamePhase.FINAL_TURNS

        # current_player_index must never point to the gone-out player
        # during the two remaining final turns
        for _ in range(4):  # more iterations than players to be safe
            assert gs.players[gs.current_player_index].id != gone_out_pid
            if gs.phase != GamePhase.FINAL_TURNS:
                break
            # Simulate that player drawing and discarding
            fp = gs.players[gs.current_player_index]
            fp.hand.append(gs.draw_pile[0])
            gs.draw_pile = gs.draw_pile[1:]
            gs.turn_phase = TurnPhase.DISCARD
            discard_id = fp.hand[0].id
            gs, err = discard_card(gs, fp.id, discard_id)
            assert err is None

    def test_final_turns_lead_to_scoring(self):
        """After all final turns are exhausted the phase must be SCORING."""
        gs = seeded_game(2)
        gone_out_idx = gs.current_player_index
        gone_out_pid = gs.players[gone_out_idx].id

        player = gs.players[gone_out_idx]
        player.hand = [
            card(Rank.KING, Suit.HEARTS),
            card(Rank.KING, Suit.DIAMONDS),
            card(Rank.KING, Suit.CLUBS),
            card(Rank.ACE, Suit.SPADES),
        ]
        gs.turn_phase = TurnPhase.DISCARD
        discard_id = next(c for c in player.hand if c.rank == Rank.ACE).id
        gs, _ = attempt_go_out(gs, gone_out_pid, discard_id)
        assert gs.phase == GamePhase.FINAL_TURNS
        assert gs.final_turns_remaining == 1

        # The one remaining player takes their final turn
        fp = gs.players[gs.current_player_index]
        fp.hand.append(gs.draw_pile[0])
        gs.draw_pile = gs.draw_pile[1:]
        gs.turn_phase = TurnPhase.DISCARD
        discard_id = fp.hand[0].id
        gs, err = discard_card(gs, fp.id, discard_id)
        assert err is None
        assert gs.phase == GamePhase.SCORING
        assert gs.last_round_results is not None and len(gs.last_round_results) == 2

    def test_second_player_goes_out_during_final_turns(self):
        """During final turns, a player with a valid hand may also go out.
        They score 0, but gone_out_player_id stays unchanged and the
        final-turn sequence continues (does not restart)."""
        gs = seeded_game(2)
        first_idx = gs.current_player_index
        first_pid = gs.players[first_idx].id
        second_idx = 1 - first_idx
        second_pid = gs.players[second_idx].id

        # Player 0 goes out from PLAYING phase
        gs.players[first_idx].hand = [
            card(Rank.KING, Suit.HEARTS),
            card(Rank.KING, Suit.DIAMONDS),
            card(Rank.KING, Suit.CLUBS),
            card(Rank.ACE, Suit.SPADES),
        ]
        gs.turn_phase = TurnPhase.DISCARD
        go_out_card = next(c for c in gs.players[first_idx].hand if c.rank == Rank.ACE).id
        gs, err = attempt_go_out(gs, first_pid, go_out_card)
        assert err is None
        assert gs.phase == GamePhase.FINAL_TURNS
        assert gs.gone_out_player_id == first_pid
        assert gs.final_turns_remaining == 1

        # Player 1 has a valid hand and also goes out during their final turn
        gs.players[second_idx].hand = [
            card(Rank.QUEEN, Suit.HEARTS),
            card(Rank.QUEEN, Suit.DIAMONDS),
            card(Rank.QUEEN, Suit.CLUBS),
            card(Rank.TWO, Suit.SPADES),
        ]
        gs.turn_phase = TurnPhase.DISCARD
        go_out_card2 = next(c for c in gs.players[second_idx].hand if c.rank == Rank.TWO).id
        gs, err = attempt_go_out(gs, second_pid, go_out_card2)
        assert err is None, f"Second go-out during final turns rejected: {err}"

        # gone_out_player_id must still be the first player
        assert gs.gone_out_player_id == first_pid
        # Second player's has_gone_out flag must be set (scores 0)
        assert gs.players[second_idx].has_gone_out is True
        # Phase must have advanced to SCORING (final turns exhausted)
        assert gs.phase == GamePhase.SCORING

    def test_second_player_goes_out_scores_zero(self):
        """compute_round_results gives 0 points to both players when both
        have has_gone_out=True."""
        gs = seeded_game(2)
        first_idx = gs.current_player_index
        first_pid = gs.players[first_idx].id
        second_idx = 1 - first_idx
        second_pid = gs.players[second_idx].id

        gs.players[first_idx].hand = [
            card(Rank.KING, Suit.HEARTS),
            card(Rank.KING, Suit.DIAMONDS),
            card(Rank.KING, Suit.CLUBS),
            card(Rank.ACE, Suit.SPADES),
        ]
        gs.turn_phase = TurnPhase.DISCARD
        go_out_card = next(c for c in gs.players[first_idx].hand if c.rank == Rank.ACE).id
        gs, _ = attempt_go_out(gs, first_pid, go_out_card)

        gs.players[second_idx].hand = [
            card(Rank.QUEEN, Suit.HEARTS),
            card(Rank.QUEEN, Suit.DIAMONDS),
            card(Rank.QUEEN, Suit.CLUBS),
            card(Rank.TWO, Suit.SPADES),
        ]
        gs.turn_phase = TurnPhase.DISCARD
        go_out_card2 = next(c for c in gs.players[second_idx].hand if c.rank == Rank.TWO).id
        gs, _ = attempt_go_out(gs, second_pid, go_out_card2)

        results = compute_round_results(gs)
        for r in results:
            assert r.round_points == 0, f"{r.player_name} expected 0 pts, got {r.round_points}"

    def test_invalid_hand_during_final_turns_rejected(self):
        """attempt_go_out during final turns must still reject an invalid hand."""
        gs = seeded_game(2)
        first_idx = gs.current_player_index
        first_pid = gs.players[first_idx].id
        second_idx = 1 - first_idx
        second_pid = gs.players[second_idx].id

        gs.players[first_idx].hand = [
            card(Rank.KING, Suit.HEARTS),
            card(Rank.KING, Suit.DIAMONDS),
            card(Rank.KING, Suit.CLUBS),
            card(Rank.ACE, Suit.SPADES),
        ]
        gs.turn_phase = TurnPhase.DISCARD
        go_out_card = next(c for c in gs.players[first_idx].hand if c.rank == Rank.ACE).id
        gs, _ = attempt_go_out(gs, first_pid, go_out_card)
        assert gs.phase == GamePhase.FINAL_TURNS

        # Player 1 has an unmatched card — cannot go out
        gs.players[second_idx].hand = [
            card(Rank.QUEEN, Suit.HEARTS),
            card(Rank.QUEEN, Suit.DIAMONDS),
            card(Rank.FIVE, Suit.CLUBS),   # unmatched
            card(Rank.TWO, Suit.SPADES),
        ]
        gs.turn_phase = TurnPhase.DISCARD
        bad_card = next(c for c in gs.players[second_idx].hand if c.rank == Rank.TWO).id
        gs, err = attempt_go_out(gs, second_pid, bad_card)
        assert err is not None
        assert gs.players[second_idx].has_gone_out is False


# ---------------------------------------------------------------------------
# compute_round_results + advance_to_next_round
# ---------------------------------------------------------------------------

class TestRoundResults:
    def test_gone_out_player_scores_zero(self):
        gs = seeded_game(2)
        gs.players[0].has_gone_out = True
        gs.players[0].hand = [card(Rank.ACE, Suit.SPADES)]  # Would be 15 pts
        results = compute_round_results(gs)
        p0_result = next(r for r in results if r.player_id == gs.players[0].id)
        assert p0_result.round_points == 0

    def test_other_player_penalised(self):
        gs = seeded_game(2)
        gs.players[0].has_gone_out = True
        gs.players[1].hand = [card(Rank.KING, Suit.SPADES)]
        results = compute_round_results(gs)
        p1_result = next(r for r in results if r.player_id == gs.players[1].id)
        assert p1_result.round_points == 10

    def test_cumulative_scores_accumulate(self):
        gs = seeded_game(2)
        gs.players[0].cumulative_score = 5
        gs.players[1].cumulative_score = 0
        gs.players[1].hand = [card(Rank.KING, Suit.SPADES)]
        compute_round_results(gs)
        assert gs.players[1].cumulative_score == 10


class TestAdvanceToNextRound:
    def test_round_increments(self):
        gs = seeded_game(2)
        gs.phase = GamePhase.SCORING
        gs = advance_to_next_round(gs)
        assert gs.round_number == 2

    def test_wild_rank_updates(self):
        gs = seeded_game(2)
        gs.phase = GamePhase.SCORING
        gs = advance_to_next_round(gs)
        assert gs.wild_rank == ROUND_WILD[2]

    def test_dealer_rotates(self):
        gs = seeded_game(2)
        old_dealer = gs.dealer_index
        gs.phase = GamePhase.SCORING
        gs = advance_to_next_round(gs)
        assert gs.dealer_index == (old_dealer + 1) % 2

    def test_after_round_11_phase_is_finished(self):
        gs = seeded_game(2)
        gs.round_number = 11
        gs.phase = GamePhase.SCORING
        gs = advance_to_next_round(gs)
        assert gs.phase == GamePhase.FINISHED

    def test_new_round_deals_cards(self):
        gs = seeded_game(2)
        gs.phase = GamePhase.SCORING
        gs = advance_to_next_round(gs)
        for p in gs.players:
            assert len(p.hand) == 4  # Round 2 → 4 cards

    def test_confirmed_by_cleared_on_advance(self):
        """next_round_confirmed_by must be empty after advancing to the new round."""
        gs = seeded_game(2)
        gs.phase = GamePhase.SCORING
        gs.next_round_confirmed_by = [gs.players[0].id, gs.players[1].id]
        gs = advance_to_next_round(gs)
        assert gs.next_round_confirmed_by == []

    def test_confirmed_by_cleared_on_finished(self):
        """next_round_confirmed_by must also be cleared when the game finishes."""
        gs = seeded_game(2)
        gs.round_number = 11
        gs.phase = GamePhase.SCORING
        gs.next_round_confirmed_by = [gs.players[0].id]
        gs = advance_to_next_round(gs)
        assert gs.phase == GamePhase.FINISHED
        assert gs.next_round_confirmed_by == []


# ---------------------------------------------------------------------------
# decks_for_players
# ---------------------------------------------------------------------------

class TestDecksForPlayers:
    def test_2_players_1_deck(self):
        assert decks_for_players(2) == 1

    def test_3_players_1_deck(self):
        assert decks_for_players(3) == 1

    def test_4_players_2_decks(self):
        assert decks_for_players(4) == 2

    def test_5_players_2_decks(self):
        assert decks_for_players(5) == 2

    def test_6_players_3_decks(self):
        assert decks_for_players(6) == 3

    def test_8_players_3_decks(self):
        assert decks_for_players(8) == 3
