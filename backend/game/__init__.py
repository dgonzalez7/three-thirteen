"""
Three-Thirteen Game Module

This module contains the core game logic, state management,
and room handling for the Three-Thirteen card game.
"""

from .state import (
    GameState, PlayerState, Card, RoomStatus, LobbyPlayer,
    GamePhase, TurnPhase, RoundResult,
)
from .engine import (
    init_game, build_deck, draw_from_pile, draw_from_discard,
    discard_card, attempt_go_out, score_hand, compute_round_results,
    advance_to_next_round,
)
from .room_manager import RoomManager
from .events import EventBus, GameEvent

__all__ = [
    "GameState", "PlayerState", "Card", "RoomStatus", "LobbyPlayer",
    "GamePhase", "TurnPhase", "RoundResult",
    "init_game", "build_deck", "draw_from_pile", "draw_from_discard",
    "discard_card", "attempt_go_out", "score_hand", "compute_round_results",
    "advance_to_next_round",
    "RoomManager",
    "EventBus", "GameEvent",
]
