from typing import List, Dict, Optional, Any
from enum import Enum
from pydantic import BaseModel
import uuid


class Suit(str, Enum):
    """Card suits"""
    HEARTS = "hearts"
    DIAMONDS = "diamonds"
    CLUBS = "clubs"
    SPADES = "spades"


class Rank(str, Enum):
    """Card ranks — in ascending order for run validation"""
    ACE = "ace"
    TWO = "two"
    THREE = "three"
    FOUR = "four"
    FIVE = "five"
    SIX = "six"
    SEVEN = "seven"
    EIGHT = "eight"
    NINE = "nine"
    TEN = "ten"
    JACK = "jack"
    QUEEN = "queen"
    KING = "king"


# Ordered rank sequence for run validation (Ace is low)
RANK_ORDER: List[Rank] = [
    Rank.ACE, Rank.TWO, Rank.THREE, Rank.FOUR, Rank.FIVE,
    Rank.SIX, Rank.SEVEN, Rank.EIGHT, Rank.NINE, Rank.TEN,
    Rank.JACK, Rank.QUEEN, Rank.KING,
]

# Penalty point values per rank
RANK_POINTS: Dict[Rank, int] = {
    Rank.ACE: 15,
    Rank.TWO: 2,
    Rank.THREE: 3,
    Rank.FOUR: 4,
    Rank.FIVE: 5,
    Rank.SIX: 6,
    Rank.SEVEN: 7,
    Rank.EIGHT: 8,
    Rank.NINE: 9,
    Rank.TEN: 10,
    Rank.JACK: 10,
    Rank.QUEEN: 10,
    Rank.KING: 10,
}

# Round number → wild rank (rounds 1–11)
ROUND_WILD: Dict[int, Rank] = {
    1: Rank.THREE,
    2: Rank.FOUR,
    3: Rank.FIVE,
    4: Rank.SIX,
    5: Rank.SEVEN,
    6: Rank.EIGHT,
    7: Rank.NINE,
    8: Rank.TEN,
    9: Rank.JACK,
    10: Rank.QUEEN,
    11: Rank.KING,
}

# Number of decks per player count
def decks_for_players(n: int) -> int:
    if n <= 3:
        return 1
    if n <= 5:
        return 2
    return 3


class GamePhase(str, Enum):
    """Active game phases (after lobby)"""
    PLAYING = "playing"
    FINAL_TURNS = "final_turns"
    SCORING = "scoring"
    FINISHED = "finished"


class TurnPhase(str, Enum):
    """Sub-phases within a single player's turn"""
    DRAW = "draw"      # Must draw before anything else
    DISCARD = "discard"  # Must discard (or go out) after drawing


class Card(BaseModel):
    """Represents a playing card"""
    id: str           # Unique within the game (rank+suit+deck_index)
    suit: Suit
    rank: Rank
    is_wild: bool = False


class PlayerState(BaseModel):
    """Per-player state during an active game"""
    id: str
    name: str
    hand: List[Card] = []
    round_score: int = 0       # Points from the current round (set at scoring)
    cumulative_score: int = 0  # Running total across all rounds
    has_gone_out: bool = False  # True for the player who went out this round


class RoundResult(BaseModel):
    """Per-player scoring result for one completed round"""
    player_id: str
    player_name: str
    round_points: int
    cumulative_score: int
    penalty_cards: List[Card] = []


class GameState(BaseModel):
    """Complete live game state for one room."""
    room_id: str
    phase: GamePhase = GamePhase.PLAYING
    turn_phase: TurnPhase = TurnPhase.DRAW
    players: List[PlayerState] = []
    dealer_index: int = 0          # Index into players of current dealer
    current_player_index: int = 0  # Index into players of active player
    draw_pile: List[Card] = []
    discard_pile: List[Card] = []
    round_number: int = 1
    wild_rank: Rank = Rank.THREE
    # Set when a player goes out; subsequent players each get one final turn
    gone_out_player_id: Optional[str] = None
    # How many final turns remain after someone goes out
    final_turns_remaining: int = 0
    # Scoring results for the most recently completed round
    last_round_results: List[RoundResult] = []
    # Players who have clicked "Start Next Round"; cleared when the new round begins
    next_round_confirmed_by: List[str] = []


class RoomStatus(str, Enum):
    """Room availability states"""
    EMPTY = "empty"
    GATHERING = "gathering"
    IN_GAME = "in_game"


class LobbyPlayer(BaseModel):
    """A player who has submitted their name in the pre-game waiting room."""
    id: str
    name: str


class RoomState(BaseModel):
    """Represents a room's state including metadata"""
    room_id: str
    room_name: str
    status: RoomStatus = RoomStatus.EMPTY
    player_count: int = 0
    player_ids: List[str] = []
    lobby_players: List[LobbyPlayer] = []
    game_state: Optional[GameState] = None
    max_players: int = 8
    min_players: int = 2
