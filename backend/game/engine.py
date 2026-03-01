from typing import List, Optional, Tuple
import random
import itertools

from .state import (
    GameState, PlayerState, Card, Suit, Rank, GamePhase, TurnPhase,
    RoundResult, RANK_ORDER, RANK_POINTS, ROUND_WILD, decks_for_players,
)


# ---------------------------------------------------------------------------
# Deck helpers
# ---------------------------------------------------------------------------

def build_deck(num_players: int, round_number: int, rng: Optional[random.Random] = None) -> List[Card]:
    """Build and shuffle a multi-deck card set with wild flags set."""
    wild_rank = ROUND_WILD[round_number]
    num_decks = decks_for_players(num_players)
    cards: List[Card] = []
    for deck_idx in range(num_decks):
        for suit in Suit:
            for rank in Rank:
                cards.append(Card(
                    id=f"{rank.value}_{suit.value}_{deck_idx}",
                    suit=suit,
                    rank=rank,
                    is_wild=(rank == wild_rank),
                ))
    r = rng or random.Random()
    r.shuffle(cards)
    return cards


# ---------------------------------------------------------------------------
# Game initialisation
# ---------------------------------------------------------------------------

def init_game(room_id: str, lobby_players: list, rng: Optional[random.Random] = None) -> GameState:
    """Create a new GameState for round 1 from the lobby player list."""
    r = rng or random.Random()
    player_list = list(lobby_players)
    r.shuffle(player_list)  # Randomise seating order

    players = [
        PlayerState(id=p.id, name=p.name)
        for p in player_list
    ]

    gs = GameState(
        room_id=room_id,
        players=players,
        dealer_index=0,
        current_player_index=1 % len(players),  # Player left of dealer goes first
        round_number=1,
        wild_rank=ROUND_WILD[1],
    )
    return _deal_round(gs, rng=r)


def _deal_round(gs: GameState, rng: Optional[random.Random] = None) -> GameState:
    """Deal cards for the current round and set up draw/discard piles."""
    cards_to_deal = gs.round_number + 2  # Round 1 → 3 cards, round 11 → 13 cards
    deck = build_deck(len(gs.players), gs.round_number, rng)

    # Deal hands
    for player in gs.players:
        player.hand = deck[:cards_to_deal]
        deck = deck[cards_to_deal:]
        player.has_gone_out = False
        player.round_score = 0

    # Turn top card face-up to start discard pile
    gs.discard_pile = [deck[0]]
    gs.draw_pile = deck[1:]
    gs.phase = GamePhase.PLAYING
    gs.turn_phase = TurnPhase.DRAW
    gs.gone_out_player_id = None
    gs.final_turns_remaining = 0
    gs.last_round_results = []
    return gs


# ---------------------------------------------------------------------------
# Turn actions — each returns (new_state, error_message | None)
# ---------------------------------------------------------------------------

def draw_from_pile(gs: GameState, player_id: str) -> Tuple[GameState, Optional[str]]:
    """Draw the top face-down card from the draw pile."""
    err = _validate_draw(gs, player_id)
    if err:
        return gs, err
    if not gs.draw_pile:
        return gs, "Draw pile is empty."

    card = gs.draw_pile[0]
    gs.draw_pile = gs.draw_pile[1:]
    player = _get_player(gs, player_id)
    player.hand.append(card)
    gs.turn_phase = TurnPhase.DISCARD
    return gs, None


def draw_from_discard(gs: GameState, player_id: str) -> Tuple[GameState, Optional[str]]:
    """Draw the top face-up card from the discard pile."""
    err = _validate_draw(gs, player_id)
    if err:
        return gs, err
    if not gs.discard_pile:
        return gs, "Discard pile is empty."

    card = gs.discard_pile[-1]
    gs.discard_pile = gs.discard_pile[:-1]
    player = _get_player(gs, player_id)
    player.hand.append(card)
    gs.turn_phase = TurnPhase.DISCARD
    return gs, None


def discard_card(gs: GameState, player_id: str, card_id: str) -> Tuple[GameState, Optional[str]]:
    """Discard a card from the player's hand and advance the turn."""
    err = _validate_discard(gs, player_id)
    if err:
        return gs, err

    player = _get_player(gs, player_id)
    card = next((c for c in player.hand if c.id == card_id), None)
    if card is None:
        return gs, "Card not in hand."

    player.hand = [c for c in player.hand if c.id != card_id]
    gs.discard_pile.append(card)
    gs = _advance_turn(gs)
    return gs, None


def attempt_go_out(gs: GameState, player_id: str, card_id: str) -> Tuple[GameState, Optional[str]]:
    """Attempt to go out by discarding card_id — validates that the remaining
    hand forms valid sets/runs with zero unmatched cards.

    During PLAYING: sets gone_out_player_id, transitions to FINAL_TURNS.
    During FINAL_TURNS: scores the player 0 (has_gone_out=True) and discards
    the card, but does NOT change gone_out_player_id or the phase — the
    existing final-turn sequence continues unchanged.
    """
    err = _validate_discard(gs, player_id)
    if err:
        return gs, err

    player = _get_player(gs, player_id)
    card = next((c for c in player.hand if c.id == card_id), None)
    if card is None:
        return gs, "Card not in hand."

    remaining = [c for c in player.hand if c.id != card_id]
    if score_hand(remaining, gs.wild_rank) != 0:
        return gs, "Cannot go out: hand has unmatched cards."

    # Discard the card in both cases
    player.hand = [c for c in player.hand if c.id != card_id]
    gs.discard_pile.append(card)
    player.has_gone_out = True

    if gs.phase == GamePhase.FINAL_TURNS:
        # Second go-out during final turns: score 0 but don't restart the sequence
        gs = _advance_turn(gs)
        return gs, None

    # First go-out (PLAYING phase): start the final-turns sequence
    gs.gone_out_player_id = player_id
    gs.phase = GamePhase.FINAL_TURNS
    gs.final_turns_remaining = len(gs.players) - 1
    gs.turn_phase = TurnPhase.DRAW
    gs = _next_player(gs)
    return gs, None


# ---------------------------------------------------------------------------
# Scoring
# ---------------------------------------------------------------------------

def score_hand(hand: List[Card], wild_rank: Rank) -> int:
    """Return the penalty score for cards not part of any valid combination.

    Tries all ways to partition the hand into sets and runs (greedy best-fit).
    Wild cards substitute for any card in a combination.
    """
    unmarked = _best_partition(hand, wild_rank)
    return sum(RANK_POINTS[c.rank] for c in unmarked)


def _best_partition(hand: List[Card], wild_rank: Rank) -> List[Card]:
    """Return the list of penalty (unmatched) cards using an exhaustive search
    on the typical small hand sizes (≤13 cards)."""
    best = list(hand)  # Worst case: everything is unmatched

    def search(remaining: List[Card], unmatched: List[Card]) -> None:
        nonlocal best
        if not remaining:
            if _penalty(unmatched) < _penalty(best):
                best = list(unmatched)
            return

        # Try to form a combination starting with remaining[0]
        card = remaining[0]
        rest = remaining[1:]
        found_any = False

        # Try sets of size ≥ 3
        for combo in _sets_containing(card, rest, wild_rank):
            found_any = True
            leftover = _remove_cards(rest, combo)
            search(leftover, unmatched)

        # Try runs of size ≥ 3
        for combo in _runs_containing(card, rest, wild_rank):
            found_any = True
            leftover = _remove_cards(rest, combo)
            search(leftover, unmatched)

        # Option: leave this card unmatched
        search(rest, unmatched + [card])

    search(list(hand), [])
    return best


def _penalty(cards: List[Card]) -> int:
    return sum(RANK_POINTS[c.rank] for c in cards)


def _is_wild(card: Card, wild_rank: Rank) -> bool:
    """A card is wild if its is_wild flag is set OR its rank matches the wild rank."""
    return card.is_wild or card.rank == wild_rank


def _sets_containing(card: Card, others: List[Card], wild_rank: Rank) -> List[List[Card]]:
    """Return all sets of size ≥ 3 that include `card` and use cards from `others`."""
    if _is_wild(card, wild_rank):
        # Wild card: two strategies —
        # 1. Delegate to each non-wild card in others as the natural anchor.
        # 2. Form a pure-wilds set when all available cards are also wilds.
        seen: set = set()
        results = []
        remaining_others = [c for c in others if c is not card]
        non_wilds = [c for c in remaining_others if not _is_wild(c, wild_rank)]

        for anchor in non_wilds:
            other_without_anchor = [c for c in remaining_others if c is not anchor]
            for combo in _sets_containing(anchor, [card] + other_without_anchor, wild_rank):
                key = frozenset(id(c) for c in combo)
                if key not in seen:
                    seen.add(key)
                    results.append(combo)

        # Pure-wilds set: card + 2 or more other wilds
        other_wilds = [c for c in remaining_others if _is_wild(c, wild_rank)]
        for size in range(2, len(other_wilds) + 1):
            group = [card] + other_wilds[:size]
            if len(group) >= 3:
                key = frozenset(id(c) for c in group)
                if key not in seen:
                    seen.add(key)
                    results.append(group)

        return results

    # Natural card anchor: same-rank cards (including wilds) can form a set.
    # Use combinations so every subset is explored — prefix slicing misses
    # subsets where naturals appear after wilds in the list.
    same_rank = [c for c in others if c.rank == card.rank or _is_wild(c, wild_rank)]
    results = []
    for size in range(2, len(same_rank) + 1):
        for combo_others in itertools.combinations(same_rank, size):
            group = [card] + list(combo_others)
            if len(group) >= 3:
                results.append(group)
    return results


def _runs_containing(card: Card, others: List[Card], wild_rank: Rank) -> List[List[Card]]:
    """Return all runs of size ≥ 3 that include `card`.

    For a natural (non-wild) card the run must share its suit.
    For a wild card, delegate to every natural card in `others` as anchor so
    the wild is used as a gap-filler or extension rather than an anchor.
    """
    if _is_wild(card, wild_rank):
        # Wild card: try it as a participant in runs anchored by each non-wild card
        seen: set = set()
        results = []
        non_wilds = [c for c in others if not _is_wild(c, wild_rank)]
        remaining_others = [c for c in others if c is not card]
        for anchor in non_wilds:
            other_without_anchor = [c for c in remaining_others if c is not anchor]
            for combo in _runs_containing(anchor, [card] + other_without_anchor, wild_rank):
                key = frozenset(id(c) for c in combo)
                if key not in seen:
                    seen.add(key)
                    results.append(combo)
        return results

    suit = card.suit
    card_pos = RANK_ORDER.index(card.rank)
    wilds = [c for c in others if _is_wild(c, wild_rank)]
    suit_cards = [c for c in others if c.suit == suit and not _is_wild(c, wild_rank)]

    results = []
    # Try all windows of rank positions that include card_pos
    for start in range(max(0, card_pos - 12), card_pos + 1):
        for length in range(3, 14):
            end = start + length
            if end > len(RANK_ORDER):
                break
            window = RANK_ORDER[start:end]
            if card.rank not in window:
                continue
            # Fill the window: use real suit cards where possible, wilds for gaps
            used_real: List[Card] = []
            used_wild: List[Card] = []
            available_wilds = list(wilds)
            ok = True
            for rank in window:
                if rank == card.rank:
                    # This is our anchor card
                    continue
                used_real_ids = {id(c) for c in used_real}
                real = next((c for c in suit_cards if c.rank == rank and id(c) not in used_real_ids), None)
                if real:
                    used_real.append(real)
                elif available_wilds:
                    used_wild.append(available_wilds.pop(0))
                else:
                    ok = False
                    break
            if ok:
                combo = [card] + used_real + used_wild
                if len(combo) >= 3:
                    results.append(combo)
    return results


def _remove_cards(cards: List[Card], to_remove: List[Card]) -> List[Card]:
    """Remove cards by object identity, so duplicate rank+suit instances
    (multi-deck games) are tracked as distinct cards."""
    remove_ids = [id(c) for c in to_remove]
    result = []
    for c in cards:
        cid = id(c)
        if cid in remove_ids:
            remove_ids.remove(cid)
        else:
            result.append(c)
    return result


# ---------------------------------------------------------------------------
# Round completion
# ---------------------------------------------------------------------------

def compute_round_results(gs: GameState) -> List[RoundResult]:
    """Score all players' hands and return results. The player who went out scores 0."""
    results = []
    for player in gs.players:
        if player.has_gone_out:
            points = 0
        else:
            points = score_hand(player.hand, gs.wild_rank)
        player.round_score = points
        player.cumulative_score += points
        results.append(RoundResult(
            player_id=player.id,
            player_name=player.name,
            round_points=points,
            cumulative_score=player.cumulative_score,
            penalty_cards=[c for c in player.hand if not _card_in_any_combo(c, player.hand, gs.wild_rank)],
        ))
    return results


def _card_in_any_combo(card: Card, hand: List[Card], wild_rank: Rank) -> bool:
    """Return True if this card ends up in a combination in the best partition."""
    unmatched = _best_partition(hand, wild_rank)
    return card not in unmatched


def advance_to_next_round(gs: GameState, rng: Optional[random.Random] = None) -> GameState:
    """Advance from scoring phase to the next round, or to FINISHED after round 11."""
    gs.next_round_confirmed_by = []
    if gs.round_number >= 11:
        gs.phase = GamePhase.FINISHED
        return gs

    gs.round_number += 1
    gs.wild_rank = ROUND_WILD[gs.round_number]
    # Dealer rotates left
    gs.dealer_index = (gs.dealer_index + 1) % len(gs.players)
    gs.current_player_index = (gs.dealer_index + 1) % len(gs.players)
    return _deal_round(gs, rng=rng)


# ---------------------------------------------------------------------------
# Private helpers
# ---------------------------------------------------------------------------

def _validate_draw(gs: GameState, player_id: str) -> Optional[str]:
    if gs.phase not in (GamePhase.PLAYING, GamePhase.FINAL_TURNS):
        return "Not in a drawable phase."
    if gs.turn_phase != TurnPhase.DRAW:
        return "You have already drawn."
    if gs.players[gs.current_player_index].id != player_id:
        return "It is not your turn."
    return None


def _validate_discard(gs: GameState, player_id: str) -> Optional[str]:
    if gs.phase not in (GamePhase.PLAYING, GamePhase.FINAL_TURNS):
        return "Not in a playable phase."
    if gs.turn_phase != TurnPhase.DISCARD:
        return "You must draw first."
    if gs.players[gs.current_player_index].id != player_id:
        return "It is not your turn."
    return None


def _get_player(gs: GameState, player_id: str) -> PlayerState:
    return next(p for p in gs.players if p.id == player_id)


def _advance_turn(gs: GameState) -> GameState:
    """After a normal discard, move to the next player (or end the round)."""
    if gs.phase == GamePhase.FINAL_TURNS:
        gs.final_turns_remaining -= 1
        if gs.final_turns_remaining <= 0:
            # All final turns done — move to scoring
            gs.phase = GamePhase.SCORING
            results = compute_round_results(gs)
            gs.last_round_results = results
            return gs

    gs = _next_player(gs)
    return gs


def _next_player(gs: GameState) -> GameState:
    """Advance current_player_index clockwise, skipping the gone-out player during FINAL_TURNS."""
    n = len(gs.players)
    for _ in range(n):
        gs.current_player_index = (gs.current_player_index + 1) % n
        candidate = gs.players[gs.current_player_index]
        # During final turns, skip the player who already went out
        if gs.phase == GamePhase.FINAL_TURNS and candidate.has_gone_out:
            continue
        break
    gs.turn_phase = TurnPhase.DRAW
    return gs
