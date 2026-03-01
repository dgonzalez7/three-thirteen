from typing import Dict, List, Optional
from fastapi import WebSocket
import asyncio

from .state import RoomState, RoomStatus, GameState, LobbyPlayer, GamePhase
from .engine import (
    init_game, draw_from_pile, draw_from_discard,
    discard_card as engine_discard, attempt_go_out as engine_go_out,
    advance_to_next_round,
)

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
        # Reverse map: player_id → room_id for cleanup on unexpected disconnect
        self.player_room_map: Dict[str, str] = {}

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
            # Allow players who are already part of this game to reconnect
            # (e.g. transitioning from PlayerLobby to GameRoom).
            # Just register their WebSocket — do not modify game state.
            if player_id in room.player_ids or any(p.id == player_id for p in room.lobby_players):
                self.room_connections[room_id][player_id] = websocket
                self.player_room_map[player_id] = room_id
                # Immediately replay the current game state so the reconnecting
                # client doesn't miss the broadcast that fired before its WS opened.
                if room.game_state is not None:
                    try:
                        await websocket.send_json({
                            "type": "game_state",
                            "game": self._player_view(room.game_state, player_id),
                        })
                    except Exception:
                        pass
                return True, ""
            else:
                return False, "A game is already in progress in this room."

        if player_id in room.player_ids:
            # Player is reconnecting (e.g. React StrictMode double-mount).
            # Just update their WebSocket reference — do not modify room state.
            self.room_connections[room_id][player_id] = websocket
            self.player_room_map[player_id] = room_id
            return True, ""

        if room.player_count >= room.max_players:
            return False, "Room is full."

        # Persist connection and reverse mapping
        self.room_connections[room_id][player_id] = websocket
        self.player_room_map[player_id] = room_id

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

        # Always remove the WebSocket connection and reverse mapping
        self.room_connections[room_id].pop(player_id, None)
        self.player_room_map.pop(player_id, None)

        if room.status == RoomStatus.IN_GAME:
            # During a game, only manage WebSocket connections.
            # handle_end_game owns all state cleanup — do not touch
            # player_ids, lobby_players, player_count, or status here.
            # Just broadcast the updated room list so the lobby reflects
            # current connection count without changing game state.
            await self._broadcast_rooms_to_lobby()
            return True

        # Not in game — normal cleanup
        if player_id in room.player_ids:
            room.player_ids.remove(player_id)
        room.player_count = len(room.player_ids)
        room.lobby_players = [p for p in room.lobby_players if p.id != player_id]

        if room.player_count == 0:
            room.status = RoomStatus.EMPTY
        else:
            room.status = RoomStatus.GATHERING

        await self._broadcast_room_update(room)
        await self._broadcast_lobby_update(room)
        return True

    # ------------------------------------------------------------------
    # Named-player lobby (join_lobby / leave_lobby)
    # ------------------------------------------------------------------

    async def handle_join_lobby(self, room_id: str, player_id: str, player_name: str) -> tuple[bool, str]:
        """Register a player's display name in the room's waiting list.

        The player must already have a WebSocket connection in the room
        (i.e. join_room must have succeeded first).
        Returns (success, error_message).
        """
        if room_id not in self.rooms:
            return False, "Room does not exist."

        room = self.rooms[room_id]

        if room.status == RoomStatus.IN_GAME:
            return False, "A game is already in progress in this room."

        if not player_name or not player_name.strip():
            return False, "Player name must not be empty."

        trimmed = player_name.strip()

        # Handle reconnect: if player_id already present, update name
        existing = next((p for p in room.lobby_players if p.id == player_id), None)
        if existing:
            existing.name = trimmed
        else:
            room.lobby_players.append(LobbyPlayer(id=player_id, name=trimmed))

        self.player_room_map[player_id] = room_id
        await self._broadcast_lobby_update(room)
        return True, ""

    async def handle_leave_lobby(self, room_id: str, player_id: str) -> bool:
        """Remove a player's named entry from the lobby list."""
        if room_id not in self.rooms:
            return False

        room = self.rooms[room_id]
        room.lobby_players = [p for p in room.lobby_players if p.id != player_id]
        self.player_room_map.pop(player_id, None)
        await self._broadcast_lobby_update(room)
        return True

    # ------------------------------------------------------------------
    # Game lifecycle
    # ------------------------------------------------------------------

    async def start_game(self, room_id: str) -> bool:
        """Transition a room from gathering → in_game (internal / test use)."""
        if room_id not in self.rooms:
            return False

        room = self.rooms[room_id]
        if room.status != RoomStatus.GATHERING:
            return False

        room.status = RoomStatus.IN_GAME
        await self._broadcast_room_update(room)
        return True

    async def handle_start_game(self, room_id: str) -> tuple[bool, str]:
        """Handle a start_game request from a player.

        Requires at least 2 named lobby players.
        Initialises GameState, broadcasts game_state to room clients.
        """
        if room_id not in self.rooms:
            return False, "Room does not exist."

        room = self.rooms[room_id]

        if room.status == RoomStatus.IN_GAME:
            return False, "Game already in progress."

        if len(room.lobby_players) < 2:
            return False, "Need at least 2 players to start."

        room.status = RoomStatus.IN_GAME
        room.game_state = init_game(room_id, room.lobby_players)

        # Notify all room clients so they navigate to GameRoom
        await self.broadcast_to_room(room_id, {
            "type": "game_starting",
            "room_id": room_id,
            "players": [p.model_dump(mode='json') for p in room.lobby_players],
        })
        # Send each player their personalised game_state view
        await self._broadcast_game_state(room_id)
        # Update the main lobby room list
        await self._broadcast_rooms_to_lobby()
        return True, ""

    # ------------------------------------------------------------------
    # In-game action handlers
    # ------------------------------------------------------------------

    async def handle_draw_card(self, room_id: str, player_id: str, source: str) -> tuple[bool, str]:
        """Handle draw_card — source is 'pile' or 'discard'."""
        room = self.rooms.get(room_id)
        if not room or not room.game_state:
            return False, "No active game."

        gs = room.game_state
        if source == "discard":
            gs, err = draw_from_discard(gs, player_id)
        else:
            gs, err = draw_from_pile(gs, player_id)

        if err:
            return False, err

        room.game_state = gs
        await self._broadcast_game_state(room_id)
        return True, ""

    async def handle_discard_card(self, room_id: str, player_id: str, card_id: str) -> tuple[bool, str]:
        """Handle discard_card."""
        room = self.rooms.get(room_id)
        if not room or not room.game_state:
            return False, "No active game."

        gs, err = engine_discard(room.game_state, player_id, card_id)
        if err:
            return False, err

        room.game_state = gs
        await self._broadcast_game_state(room_id)

        if gs.phase == GamePhase.SCORING:
            await self._broadcast_round_over(room_id)

        return True, ""

    async def handle_go_out(self, room_id: str, player_id: str, card_id: str) -> tuple[bool, str]:
        """Handle go_out attempt."""
        room = self.rooms.get(room_id)
        if not room or not room.game_state:
            return False, "No active game."

        gs, err = engine_go_out(room.game_state, player_id, card_id)
        if err:
            return False, err

        room.game_state = gs

        # Notify all players that someone went out (before game_state so UI
        # can display the notification together with the turn change)
        gone_out_player = next(p for p in gs.players if p.id == player_id)
        await self.broadcast_to_room(room_id, {
            "type": "player_went_out",
            "player_id": player_id,
            "player_name": gone_out_player.name,
            "final_turns_remaining": gs.final_turns_remaining,
        })

        await self._broadcast_game_state(room_id)

        if gs.phase == GamePhase.SCORING:
            await self._broadcast_round_over(room_id)

        return True, ""

    async def handle_next_round(self, room_id: str, player_id: str) -> tuple[bool, str]:
        """Record a player's confirmation to start the next round.

        Each player must click once. The round advances only when every player
        in the room has confirmed. After each click the updated state is
        broadcast so unconfirmed players see the button while confirmed ones
        see 'Waiting for others…'.
        """
        room = self.rooms.get(room_id)
        if not room or not room.game_state:
            return False, "No active game."

        gs = room.game_state
        if gs.phase not in (GamePhase.SCORING, GamePhase.FINISHED):
            return False, "Round is not over yet."

        if player_id in gs.next_round_confirmed_by:
            return True, ""  # Duplicate click — already confirmed

        gs.next_round_confirmed_by.append(player_id)
        room.game_state = gs

        all_confirmed = all(
            p.id in gs.next_round_confirmed_by for p in gs.players
        )

        if not all_confirmed:
            await self._broadcast_game_state(room_id)
            return True, ""

        gs = advance_to_next_round(gs)
        room.game_state = gs

        if gs.phase == GamePhase.FINISHED:
            await self._broadcast_game_finished(room_id)
        else:
            await self._broadcast_game_state(room_id)

        return True, ""

    async def handle_end_game(self, room_id: str) -> bool:
        """Reset a room after a game ends — clears all players and lobby list.

        Snapshots connections before any state changes so a simultaneous
        leave_room cannot remove clients from the dict mid-broadcast.
        Broadcasts lobby_reset directly (bypassing broadcast_to_room) to
        avoid leave_room being called on failed sends during teardown.
        """
        if room_id not in self.rooms:
            return False

        room = self.rooms[room_id]

        # Snapshot connections before any state changes so a simultaneous
        # leave_room cannot remove clients from the dict mid-broadcast
        connections_snapshot = dict(self.room_connections[room_id])

        # Broadcast lobby_reset directly to snapshot — bypass broadcast_to_room
        # to avoid leave_room being called on failed sends during teardown
        for player_id, ws in connections_snapshot.items():
            try:
                await ws.send_json({"type": "lobby_reset", "room_id": room_id})
            except Exception:
                pass  # Client already disconnected — that's fine

        # Now clear all state
        players_to_clear = list(room.player_ids)
        room.status = RoomStatus.EMPTY
        room.player_ids = []
        room.lobby_players = []
        room.player_count = 0
        room.game_state = None
        self.room_connections[room_id] = {}
        for pid in players_to_clear:
            self.player_room_map.pop(pid, None)

        await self._broadcast_rooms_to_lobby()
        return True

    async def end_game(self, room_id: str) -> bool:
        """Alias kept for backward-compat with existing tests."""
        return await self.handle_end_game(room_id)

    # ------------------------------------------------------------------
    # Game-state broadcast helpers
    # ------------------------------------------------------------------

    def _player_view(self, gs: GameState, viewer_id: str) -> dict:
        """Build a serialisable game-state dict for a specific player.

        Other players' hands are hidden (replaced with card count).
        Draw pile is hidden (only count exposed).
        """
        data = gs.model_dump(mode='json')
        # Hide other players' hands
        for p in data['players']:
            if p['id'] != viewer_id:
                p['hand_count'] = len(p['hand'])
                p['hand'] = []  # Do not leak other players' cards
        # Hide draw pile contents — only expose count
        data['draw_pile_count'] = len(data['draw_pile'])
        data['draw_pile'] = []
        return data

    async def _broadcast_game_state(self, room_id: str) -> None:
        """Send each connected player their personalised game_state view."""
        room = self.rooms.get(room_id)
        if not room or not room.game_state:
            return
        gs = room.game_state
        disconnected = []
        for player_id, ws in list(self.room_connections[room_id].items()):
            try:
                await ws.send_json({
                    "type": "game_state",
                    "game": self._player_view(gs, player_id),
                })
            except Exception:
                disconnected.append(player_id)
        for pid in disconnected:
            await self.leave_room(room_id, pid)

    async def _broadcast_round_over(self, room_id: str) -> None:
        """Broadcast round_over with full scoring results."""
        room = self.rooms.get(room_id)
        if not room or not room.game_state:
            return
        gs = room.game_state
        await self.broadcast_to_room(room_id, {
            "type": "round_over",
            "round_number": gs.round_number,
            "results": [r.model_dump(mode='json') for r in gs.last_round_results],
        })

    async def _broadcast_game_finished(self, room_id: str) -> None:
        """Broadcast game_finished with final leaderboard."""
        room = self.rooms.get(room_id)
        if not room or not room.game_state:
            return
        gs = room.game_state
        leaderboard = sorted(
            [{"id": p.id, "name": p.name, "score": p.cumulative_score} for p in gs.players],
            key=lambda x: x["score"]
        )
        await self.broadcast_to_room(room_id, {
            "type": "game_finished",
            "leaderboard": leaderboard,
        })

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
            "room": room.model_dump(mode='json'),
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

    async def _broadcast_rooms_to_lobby(self) -> None:
        """Send the current rooms snapshot to all lobby watchers."""
        rooms_payload = self._rooms_snapshot_payload()
        disconnected_lobby = []
        for conn_id, ws in list(self.lobby_connections.items()):
            try:
                await ws.send_json(rooms_payload)
            except Exception:
                disconnected_lobby.append(conn_id)
        for conn_id in disconnected_lobby:
            self.lobby_connections.pop(conn_id, None)

    async def _broadcast_lobby_update(self, room: RoomState) -> None:
        """Send a lobby_update message to all WebSocket clients in a room."""
        payload = {
            "type": "lobby_update",
            "room_id": room.room_id,
            "players": [p.model_dump(mode='json') for p in room.lobby_players],
            "status": room.status.value,
        }
        disconnected = []
        for player_id, ws in list(self.room_connections[room.room_id].items()):
            try:
                await ws.send_json(payload)
            except Exception:
                disconnected.append(player_id)
        for player_id in disconnected:
            await self.leave_room(room.room_id, player_id)

    async def _send_rooms_snapshot(self, websocket: WebSocket) -> None:
        """Send the current room list snapshot to a single client."""
        try:
            await websocket.send_json(self._rooms_snapshot_payload())
        except Exception:
            pass

    def _rooms_snapshot_payload(self) -> dict:
        return {
            "type": "rooms_update",
            "rooms": [r.model_dump(mode='json') for r in self.rooms.values()],
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
