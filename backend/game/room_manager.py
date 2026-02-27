from typing import Dict, List, Optional
from fastapi import WebSocket
import asyncio

from .state import RoomState, RoomStatus, GameState, Player

NUM_ROOMS = 10

class RoomManager:
    """Manages the fixed set of 10 game rooms and all player connections.

    Rooms are pre-created at startup and never destroyed. Each room
    transitions between empty → gathering → in_game → empty.
    All lobby clients are notified whenever any room's state changes.
    """

    def __init__(self):
        # Fixed 10 rooms keyed by room_id ("room-1" … "room-10")
        self.rooms: Dict[str, RoomState] = {}
        # Connections inside a specific game room: room_id → {player_id: ws}
        self.room_connections: Dict[str, Dict[str, WebSocket]] = {}
        # Lobby connections (clients on the lobby screen): connection_id → ws
        self.lobby_connections: Dict[str, WebSocket] = {}

        self._init_rooms()

    # ------------------------------------------------------------------
    # Initialisation
    # ------------------------------------------------------------------

    def _init_rooms(self) -> None:
        """Create the fixed 10 rooms at startup."""
        for i in range(1, NUM_ROOMS + 1):
            room_id = f"room-{i}"
            self.rooms[room_id] = RoomState(
                room_id=room_id,
                room_name=f"Room {i}",
            )
            self.room_connections[room_id] = {}

    # ------------------------------------------------------------------
    # Lobby connections (clients watching the room list)
    # ------------------------------------------------------------------

    async def register_lobby_connection(self, connection_id: str, websocket: WebSocket) -> None:
        """Register a client that is on the lobby screen."""
        self.lobby_connections[connection_id] = websocket
        # Immediately send current room list to the new client
        await self._send_rooms_snapshot(websocket)

    async def unregister_lobby_connection(self, connection_id: str) -> None:
        """Remove a lobby client (e.g. on disconnect or when they enter a room)."""
        self.lobby_connections.pop(connection_id, None)

    # ------------------------------------------------------------------
    # Room join / leave
    # ------------------------------------------------------------------

    async def join_room(self, room_id: str, player_id: str, websocket: WebSocket) -> tuple[bool, str]:
        """Attempt to add a player to a room.

        Returns (success, error_message).
        Fails if the room does not exist or is in_game.
        """
        if room_id not in self.rooms:
            return False, "Room does not exist."

        room = self.rooms[room_id]

        if room.status == RoomStatus.IN_GAME:
            return False, "A game is already in progress in this room."

        if player_id in room.player_ids:
            return False, "Player already in room."

        if room.player_count >= room.max_players:
            return False, "Room is full."

        # Persist connection
        self.room_connections[room_id][player_id] = websocket

        # Update room state
        room.player_ids.append(player_id)
        room.player_count = len(room.player_ids)
        room.status = RoomStatus.GATHERING

        await self._broadcast_room_update(room)
        return True, ""

    async def leave_room(self, room_id: str, player_id: str) -> bool:
        """Remove a player from a room and update room status."""
        if room_id not in self.rooms:
            return False

        room = self.rooms[room_id]

        # Remove connection
        self.room_connections[room_id].pop(player_id, None)

        # Update player list
        if player_id in room.player_ids:
            room.player_ids.remove(player_id)
        room.player_count = len(room.player_ids)

        # Transition status: if no players left the room goes back to empty
        if room.player_count == 0:
            room.status = RoomStatus.EMPTY
        elif room.status != RoomStatus.IN_GAME:
            room.status = RoomStatus.GATHERING

        await self._broadcast_room_update(room)
        return True

    # ------------------------------------------------------------------
    # Game lifecycle (called by the game engine later)
    # ------------------------------------------------------------------

    async def start_game(self, room_id: str) -> bool:
        """Transition a room from gathering → in_game."""
        if room_id not in self.rooms:
            return False

        room = self.rooms[room_id]
        if room.status != RoomStatus.GATHERING:
            return False

        room.status = RoomStatus.IN_GAME
        await self._broadcast_room_update(room)
        return True

    async def end_game(self, room_id: str) -> bool:
        """Transition a room from in_game → empty and clear players."""
        if room_id not in self.rooms:
            return False

        room = self.rooms[room_id]
        room.status = RoomStatus.EMPTY
        room.player_ids = []
        room.player_count = 0
        room.game_state = None
        self.room_connections[room_id] = {}

        await self._broadcast_room_update(room)
        return True

    # ------------------------------------------------------------------
    # Broadcast helpers
    # ------------------------------------------------------------------

    async def _broadcast_room_update(self, room: RoomState) -> None:
        """Push a rooms_update event carrying the full room list to every
        connected lobby client, plus a targeted room_state event to clients
        inside the affected room."""
        rooms_payload = self._rooms_snapshot_payload()

        # Broadcast full snapshot to all lobby watchers
        disconnected_lobby = []
        for conn_id, ws in list(self.lobby_connections.items()):
            try:
                await ws.send_json(rooms_payload)
            except Exception:
                disconnected_lobby.append(conn_id)
        for conn_id in disconnected_lobby:
            self.lobby_connections.pop(conn_id, None)

        # Also notify players inside the room
        room_event = {
            "type": "room_state",
            "room": room.model_dump(),
        }
        disconnected_room = []
        for player_id, ws in list(self.room_connections[room.room_id].items()):
            try:
                await ws.send_json(room_event)
            except Exception:
                disconnected_room.append(player_id)
        for player_id in disconnected_room:
            await self.leave_room(room.room_id, player_id)

    async def broadcast_to_room(self, room_id: str, message: dict) -> int:
        """Broadcast an arbitrary message to all players inside a room."""
        if room_id not in self.room_connections:
            return 0

        sent_count = 0
        disconnected = []

        for player_id, ws in list(self.room_connections[room_id].items()):
            try:
                await ws.send_json(message)
                sent_count += 1
            except Exception:
                disconnected.append(player_id)

        for player_id in disconnected:
            await self.leave_room(room_id, player_id)

        return sent_count

    async def _send_rooms_snapshot(self, websocket: WebSocket) -> None:
        """Send the current room list snapshot to a single client."""
        try:
            await websocket.send_json(self._rooms_snapshot_payload())
        except Exception:
            pass

    def _rooms_snapshot_payload(self) -> dict:
        return {
            "type": "rooms_update",
            "rooms": [r.model_dump() for r in self.rooms.values()],
        }

    # ------------------------------------------------------------------
    # Read helpers
    # ------------------------------------------------------------------

    def get_room(self, room_id: str) -> Optional[RoomState]:
        """Return room state by ID."""
        return self.rooms.get(room_id)

    def get_all_rooms(self) -> List[RoomState]:
        """Return all 10 rooms in order."""
        return list(self.rooms.values())
