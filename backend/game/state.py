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
    """Card ranks"""
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

class GamePhase(str, Enum):
    """Game phases"""
    LOBBY = "lobby"
    JOINING = "joining"
    DEALING = "dealing"
    PLAYING = "playing"
    SCORING = "scoring"
    FINISHED = "finished"

class Card(BaseModel):
    """Represents a playing card"""
    suit: Suit
    rank: Rank
    is_wild: bool = False
    
    # TODO: Add card comparison methods
    # TODO: Add card display methods

class Player(BaseModel):
    """Represents a player in the game"""
    id: str
    name: str
    hand: List[Card] = []
    score: int = 0
    is_active: bool = True
    
    # TODO: Add player action validation
    # TODO: Add scoring calculation methods

class GameState(BaseModel):
    """Represents the complete game state"""
    room_id: str
    phase: GamePhase = GamePhase.LOBBY
    players: List[Player] = []
    current_player_index: int = 0
    deck: List[Card] = []
    discard_pile: List[Card] = []
    round_number: int = 1
    wild_rank: Optional[Rank] = None
    
    # TODO: Add state transition validation
    # TODO: Add immutable state update methods
    # TODO: Add game state serialization

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
    min_players: int = 4
