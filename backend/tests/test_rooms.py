import pytest
from unittest.mock import AsyncMock, MagicMock
from fastapi import WebSocket

from game.room_manager import RoomManager, NUM_ROOMS
from game.state import RoomStatus, LobbyPlayer


def make_ws() -> MagicMock:
    """Return a mock WebSocket whose async methods work correctly."""
    ws = MagicMock(spec=WebSocket)
    ws.send_json = AsyncMock()
    ws.receive_text = AsyncMock(return_value="ping")
    return ws


@pytest.fixture
def rm() -> RoomManager:
    """Fresh RoomManager for each test."""
    return RoomManager()


# ---------------------------------------------------------------------------
# Initialisation
# ---------------------------------------------------------------------------

class TestInitialisation:
    def test_creates_ten_rooms(self, rm):
        assert len(rm.rooms) == NUM_ROOMS

    def test_room_ids_are_room_1_through_10(self, rm):
        expected = {f"room-{i}" for i in range(1, NUM_ROOMS + 1)}
        assert set(rm.rooms.keys()) == expected

    def test_all_rooms_start_empty(self, rm):
        for room in rm.rooms.values():
            assert room.status == RoomStatus.EMPTY

    def test_all_rooms_start_with_zero_players(self, rm):
        for room in rm.rooms.values():
            assert room.player_count == 0
            assert room.player_ids == []

    def test_room_names_match_ids(self, rm):
        for i in range(1, NUM_ROOMS + 1):
            room = rm.rooms[f"room-{i}"]
            assert room.room_name == f"Room {i}"

    def test_get_all_rooms_returns_ten(self, rm):
        assert len(rm.get_all_rooms()) == NUM_ROOMS


# ---------------------------------------------------------------------------
# Lobby connections
# ---------------------------------------------------------------------------

class TestLobbyConnections:
    @pytest.mark.asyncio
    async def test_register_lobby_sends_snapshot(self, rm):
        ws = make_ws()
        await rm.register_lobby_connection("conn-1", ws)
        ws.send_json.assert_awaited_once()
        payload = ws.send_json.call_args[0][0]
        assert payload["type"] == "rooms_update"
        assert len(payload["rooms"]) == NUM_ROOMS

    @pytest.mark.asyncio
    async def test_unregister_lobby_removes_connection(self, rm):
        ws = make_ws()
        await rm.register_lobby_connection("conn-1", ws)
        await rm.unregister_lobby_connection("conn-1")
        assert "conn-1" not in rm.lobby_connections

    @pytest.mark.asyncio
    async def test_unregister_unknown_connection_is_safe(self, rm):
        """Unregistering a connection that was never added must not raise."""
        await rm.unregister_lobby_connection("does-not-exist")


# ---------------------------------------------------------------------------
# join_room — happy path
# ---------------------------------------------------------------------------

class TestJoinRoom:
    @pytest.mark.asyncio
    async def test_join_empty_room_succeeds(self, rm):
        ws = make_ws()
        ok, msg = await rm.join_room("room-1", "p1", ws)
        assert ok is True
        assert msg == ""

    @pytest.mark.asyncio
    async def test_join_transitions_empty_to_gathering(self, rm):
        ws = make_ws()
        await rm.join_room("room-1", "p1", ws)
        assert rm.rooms["room-1"].status == RoomStatus.GATHERING

    @pytest.mark.asyncio
    async def test_join_increments_player_count(self, rm):
        await rm.join_room("room-1", "p1", make_ws())
        await rm.join_room("room-1", "p2", make_ws())
        assert rm.rooms["room-1"].player_count == 2

    @pytest.mark.asyncio
    async def test_join_adds_player_id_to_list(self, rm):
        ws = make_ws()
        await rm.join_room("room-1", "alice", ws)
        assert "alice" in rm.rooms["room-1"].player_ids

    @pytest.mark.asyncio
    async def test_join_stores_websocket_connection(self, rm):
        ws = make_ws()
        await rm.join_room("room-1", "p1", ws)
        assert rm.room_connections["room-1"]["p1"] is ws

    @pytest.mark.asyncio
    async def test_join_broadcasts_rooms_update_to_lobby(self, rm):
        lobby_ws = make_ws()
        await rm.register_lobby_connection("lobby-1", lobby_ws)
        lobby_ws.send_json.reset_mock()

        await rm.join_room("room-1", "p1", make_ws())

        lobby_ws.send_json.assert_awaited_once()
        payload = lobby_ws.send_json.call_args[0][0]
        assert payload["type"] == "rooms_update"

    @pytest.mark.asyncio
    async def test_join_gathering_room_succeeds(self, rm):
        """A second player can join a gathering room."""
        await rm.join_room("room-1", "p1", make_ws())
        ok, _ = await rm.join_room("room-1", "p2", make_ws())
        assert ok is True


# ---------------------------------------------------------------------------
# join_room — failure cases
# ---------------------------------------------------------------------------

class TestJoinRoomFailures:
    @pytest.mark.asyncio
    async def test_join_nonexistent_room_fails(self, rm):
        ok, msg = await rm.join_room("room-99", "p1", make_ws())
        assert ok is False
        assert msg != ""

    @pytest.mark.asyncio
    async def test_join_in_game_room_fails(self, rm):
        await rm.join_room("room-1", "p1", make_ws())
        await rm.join_room("room-1", "p2", make_ws())
        await rm.join_room("room-1", "p3", make_ws())
        await rm.join_room("room-1", "p4", make_ws())
        await rm.start_game("room-1")

        ok, msg = await rm.join_room("room-1", "p5", make_ws())
        assert ok is False
        assert "in progress" in msg.lower()

    @pytest.mark.asyncio
    async def test_join_duplicate_player_fails(self, rm):
        ws = make_ws()
        await rm.join_room("room-1", "p1", ws)
        ok, msg = await rm.join_room("room-1", "p1", make_ws())
        assert ok is False
        assert msg != ""

    @pytest.mark.asyncio
    async def test_join_full_room_fails(self, rm):
        for i in range(8):
            await rm.join_room("room-1", f"p{i}", make_ws())
        ok, msg = await rm.join_room("room-1", "p_extra", make_ws())
        assert ok is False
        assert msg != ""


# ---------------------------------------------------------------------------
# leave_room
# ---------------------------------------------------------------------------

class TestLeaveRoom:
    @pytest.mark.asyncio
    async def test_leave_removes_player(self, rm):
        await rm.join_room("room-1", "p1", make_ws())
        await rm.leave_room("room-1", "p1")
        assert "p1" not in rm.rooms["room-1"].player_ids

    @pytest.mark.asyncio
    async def test_leave_decrements_count(self, rm):
        await rm.join_room("room-1", "p1", make_ws())
        await rm.join_room("room-1", "p2", make_ws())
        await rm.leave_room("room-1", "p1")
        assert rm.rooms["room-1"].player_count == 1

    @pytest.mark.asyncio
    async def test_leave_last_player_transitions_to_empty(self, rm):
        await rm.join_room("room-1", "p1", make_ws())
        await rm.leave_room("room-1", "p1")
        assert rm.rooms["room-1"].status == RoomStatus.EMPTY

    @pytest.mark.asyncio
    async def test_leave_partial_stays_gathering(self, rm):
        await rm.join_room("room-1", "p1", make_ws())
        await rm.join_room("room-1", "p2", make_ws())
        await rm.leave_room("room-1", "p1")
        assert rm.rooms["room-1"].status == RoomStatus.GATHERING

    @pytest.mark.asyncio
    async def test_leave_removes_websocket_connection(self, rm):
        ws = make_ws()
        await rm.join_room("room-1", "p1", ws)
        await rm.leave_room("room-1", "p1")
        assert "p1" not in rm.room_connections["room-1"]

    @pytest.mark.asyncio
    async def test_leave_nonexistent_room_returns_false(self, rm):
        result = await rm.leave_room("room-99", "p1")
        assert result is False

    @pytest.mark.asyncio
    async def test_leave_player_not_in_room_is_safe(self, rm):
        """Leaving a room you are not in should not raise."""
        result = await rm.leave_room("room-1", "ghost")
        assert result is True

    @pytest.mark.asyncio
    async def test_leave_during_game_does_not_change_to_empty(self, rm):
        """If a player leaves a room that is in_game, status stays in_game
        until end_game is called (the game engine decides what to do)."""
        for p in ["p1", "p2", "p3", "p4"]:
            await rm.join_room("room-1", p, make_ws())
        await rm.start_game("room-1")
        await rm.leave_room("room-1", "p1")
        assert rm.rooms["room-1"].status == RoomStatus.IN_GAME


# ---------------------------------------------------------------------------
# Game lifecycle (start_game / end_game)
# ---------------------------------------------------------------------------

class TestGameLifecycle:
    @pytest.mark.asyncio
    async def test_start_game_transitions_to_in_game(self, rm):
        for p in ["p1", "p2", "p3", "p4"]:
            await rm.join_room("room-1", p, make_ws())
        ok = await rm.start_game("room-1")
        assert ok is True
        assert rm.rooms["room-1"].status == RoomStatus.IN_GAME

    @pytest.mark.asyncio
    async def test_start_game_on_empty_room_fails(self, rm):
        ok = await rm.start_game("room-1")
        assert ok is False

    @pytest.mark.asyncio
    async def test_start_game_on_in_game_room_fails(self, rm):
        for p in ["p1", "p2", "p3", "p4"]:
            await rm.join_room("room-1", p, make_ws())
        await rm.start_game("room-1")
        ok = await rm.start_game("room-1")
        assert ok is False

    @pytest.mark.asyncio
    async def test_start_game_nonexistent_room_fails(self, rm):
        ok = await rm.start_game("room-99")
        assert ok is False

    @pytest.mark.asyncio
    async def test_end_game_transitions_to_empty(self, rm):
        for p in ["p1", "p2", "p3", "p4"]:
            await rm.join_room("room-1", p, make_ws())
        await rm.start_game("room-1")
        ok = await rm.end_game("room-1")
        assert ok is True
        assert rm.rooms["room-1"].status == RoomStatus.EMPTY

    @pytest.mark.asyncio
    async def test_end_game_clears_players(self, rm):
        for p in ["p1", "p2", "p3", "p4"]:
            await rm.join_room("room-1", p, make_ws())
        await rm.start_game("room-1")
        await rm.end_game("room-1")
        assert rm.rooms["room-1"].player_count == 0
        assert rm.rooms["room-1"].player_ids == []

    @pytest.mark.asyncio
    async def test_end_game_clears_connections(self, rm):
        for p in ["p1", "p2", "p3", "p4"]:
            await rm.join_room("room-1", p, make_ws())
        await rm.start_game("room-1")
        await rm.end_game("room-1")
        assert rm.room_connections["room-1"] == {}

    @pytest.mark.asyncio
    async def test_end_game_nonexistent_room_fails(self, rm):
        ok = await rm.end_game("room-99")
        assert ok is False

    @pytest.mark.asyncio
    async def test_room_is_joinable_again_after_end_game(self, rm):
        for p in ["p1", "p2", "p3", "p4"]:
            await rm.join_room("room-1", p, make_ws())
        await rm.start_game("room-1")
        await rm.end_game("room-1")
        ok, _ = await rm.join_room("room-1", "new_player", make_ws())
        assert ok is True


# ---------------------------------------------------------------------------
# Full state-transition sequence
# ---------------------------------------------------------------------------

class TestStateTransitionSequence:
    @pytest.mark.asyncio
    async def test_full_lifecycle(self, rm):
        """empty → gathering → in_game → empty → gathering"""
        room = rm.rooms["room-1"]
        assert room.status == RoomStatus.EMPTY

        await rm.join_room("room-1", "p1", make_ws())
        assert room.status == RoomStatus.GATHERING

        for p in ["p2", "p3", "p4"]:
            await rm.join_room("room-1", p, make_ws())
        await rm.start_game("room-1")
        assert room.status == RoomStatus.IN_GAME

        await rm.end_game("room-1")
        assert room.status == RoomStatus.EMPTY

        await rm.join_room("room-1", "newcomer", make_ws())
        assert room.status == RoomStatus.GATHERING

    @pytest.mark.asyncio
    async def test_multiple_rooms_are_independent(self, rm):
        await rm.join_room("room-1", "p1", make_ws())
        assert rm.rooms["room-1"].status == RoomStatus.GATHERING
        assert rm.rooms["room-2"].status == RoomStatus.EMPTY


# ---------------------------------------------------------------------------
# handle_join_lobby
# ---------------------------------------------------------------------------

class TestHandleJoinLobby:
    @pytest.mark.asyncio
    async def test_join_lobby_adds_named_player(self, rm):
        await rm.join_room("room-1", "p1", make_ws())
        ok, err = await rm.handle_join_lobby("room-1", "p1", "Alice")
        assert ok is True
        assert err == ""
        assert any(p.name == "Alice" for p in rm.rooms["room-1"].lobby_players)

    @pytest.mark.asyncio
    async def test_join_lobby_trims_name(self, rm):
        await rm.join_room("room-1", "p1", make_ws())
        await rm.handle_join_lobby("room-1", "p1", "  Alice  ")
        assert rm.rooms["room-1"].lobby_players[0].name == "Alice"

    @pytest.mark.asyncio
    async def test_join_lobby_rejects_empty_name(self, rm):
        await rm.join_room("room-1", "p1", make_ws())
        ok, err = await rm.handle_join_lobby("room-1", "p1", "   ")
        assert ok is False
        assert err != ""

    @pytest.mark.asyncio
    async def test_join_lobby_rejects_nonexistent_room(self, rm):
        ok, err = await rm.handle_join_lobby("room-99", "p1", "Alice")
        assert ok is False

    @pytest.mark.asyncio
    async def test_join_lobby_rejects_in_game_room(self, rm):
        for pid, name in [("p1", "Alice"), ("p2", "Bob")]:
            await rm.join_room("room-1", pid, make_ws())
            await rm.handle_join_lobby("room-1", pid, name)
        await rm.handle_start_game("room-1")
        ok, err = await rm.handle_join_lobby("room-1", "p1", "Alice")
        assert ok is False
        assert "in progress" in err.lower()

    @pytest.mark.asyncio
    async def test_join_lobby_handles_reconnect_by_updating_name(self, rm):
        """If a player_id already exists in lobby_players, the name is updated."""
        await rm.join_room("room-1", "p1", make_ws())
        await rm.handle_join_lobby("room-1", "p1", "Alice")
        ok, _ = await rm.handle_join_lobby("room-1", "p1", "Alice Updated")
        assert ok is True
        assert rm.rooms["room-1"].lobby_players[0].name == "Alice Updated"
        assert len(rm.rooms["room-1"].lobby_players) == 1

    @pytest.mark.asyncio
    async def test_join_lobby_broadcasts_lobby_update_to_room(self, rm):
        ws = make_ws()
        await rm.join_room("room-1", "p1", ws)
        ws.send_json.reset_mock()
        await rm.handle_join_lobby("room-1", "p1", "Alice")
        calls = [c[0][0] for c in ws.send_json.call_args_list]
        assert any(c.get("type") == "lobby_update" for c in calls)

    @pytest.mark.asyncio
    async def test_join_lobby_update_includes_all_players(self, rm):
        ws1, ws2 = make_ws(), make_ws()
        await rm.join_room("room-1", "p1", ws1)
        await rm.join_room("room-1", "p2", ws2)
        await rm.handle_join_lobby("room-1", "p1", "Alice")
        await rm.handle_join_lobby("room-1", "p2", "Bob")
        calls = [c[0][0] for c in ws2.send_json.call_args_list]
        lobby_updates = [c for c in calls if c.get("type") == "lobby_update"]
        last = lobby_updates[-1]
        names = [p["name"] for p in last["players"]]
        assert "Alice" in names and "Bob" in names


# ---------------------------------------------------------------------------
# handle_leave_lobby
# ---------------------------------------------------------------------------

class TestHandleLeaveLobby:
    @pytest.mark.asyncio
    async def test_leave_lobby_removes_player(self, rm):
        await rm.join_room("room-1", "p1", make_ws())
        await rm.handle_join_lobby("room-1", "p1", "Alice")
        await rm.handle_leave_lobby("room-1", "p1")
        assert not any(p.id == "p1" for p in rm.rooms["room-1"].lobby_players)

    @pytest.mark.asyncio
    async def test_leave_lobby_broadcasts_update(self, rm):
        ws = make_ws()
        await rm.join_room("room-1", "p1", ws)
        await rm.handle_join_lobby("room-1", "p1", "Alice")
        ws.send_json.reset_mock()
        await rm.handle_leave_lobby("room-1", "p1")
        calls = [c[0][0] for c in ws.send_json.call_args_list]
        assert any(c.get("type") == "lobby_update" for c in calls)

    @pytest.mark.asyncio
    async def test_leave_lobby_nonexistent_room_returns_false(self, rm):
        result = await rm.handle_leave_lobby("room-99", "p1")
        assert result is False

    @pytest.mark.asyncio
    async def test_leave_room_also_clears_lobby_player(self, rm):
        """A full WebSocket disconnect must also clean up the lobby player list."""
        await rm.join_room("room-1", "p1", make_ws())
        await rm.handle_join_lobby("room-1", "p1", "Alice")
        await rm.leave_room("room-1", "p1")
        assert not any(p.id == "p1" for p in rm.rooms["room-1"].lobby_players)


# ---------------------------------------------------------------------------
# handle_start_game
# ---------------------------------------------------------------------------

class TestHandleStartGame:
    @pytest.mark.asyncio
    async def test_start_game_requires_two_lobby_players(self, rm):
        await rm.join_room("room-1", "p1", make_ws())
        await rm.handle_join_lobby("room-1", "p1", "Alice")
        ok, err = await rm.handle_start_game("room-1")
        assert ok is False
        assert "2" in err or "least" in err.lower()

    @pytest.mark.asyncio
    async def test_start_game_transitions_to_in_game(self, rm):
        for pid, name in [("p1", "Alice"), ("p2", "Bob")]:
            await rm.join_room("room-1", pid, make_ws())
            await rm.handle_join_lobby("room-1", pid, name)
        ok, _ = await rm.handle_start_game("room-1")
        assert ok is True
        assert rm.rooms["room-1"].status == RoomStatus.IN_GAME

    @pytest.mark.asyncio
    async def test_start_game_broadcasts_game_starting_to_room(self, rm):
        ws1, ws2 = make_ws(), make_ws()
        for ws, pid, name in [(ws1, "p1", "Alice"), (ws2, "p2", "Bob")]:
            await rm.join_room("room-1", pid, ws)
            await rm.handle_join_lobby("room-1", pid, name)
        ws1.send_json.reset_mock()
        ws2.send_json.reset_mock()
        await rm.handle_start_game("room-1")
        calls = [c[0][0] for c in ws1.send_json.call_args_list]
        assert any(c.get("type") == "game_starting" for c in calls)

    @pytest.mark.asyncio
    async def test_start_game_game_starting_includes_players(self, rm):
        ws1, ws2 = make_ws(), make_ws()
        for ws, pid, name in [(ws1, "p1", "Alice"), (ws2, "p2", "Bob")]:
            await rm.join_room("room-1", pid, ws)
            await rm.handle_join_lobby("room-1", pid, name)
        await rm.handle_start_game("room-1")
        calls = [c[0][0] for c in ws1.send_json.call_args_list]
        game_starting = next(c for c in calls if c.get("type") == "game_starting")
        names = [p["name"] for p in game_starting["players"]]
        assert "Alice" in names and "Bob" in names

    @pytest.mark.asyncio
    async def test_start_game_broadcasts_rooms_update_to_lobby(self, rm):
        lobby_ws = make_ws()
        await rm.register_lobby_connection("lobby-1", lobby_ws)
        for pid, name in [("p1", "Alice"), ("p2", "Bob")]:
            await rm.join_room("room-1", pid, make_ws())
            await rm.handle_join_lobby("room-1", pid, name)
        lobby_ws.send_json.reset_mock()
        await rm.handle_start_game("room-1")
        calls = [c[0][0] for c in lobby_ws.send_json.call_args_list]
        assert any(c.get("type") == "rooms_update" for c in calls)

    @pytest.mark.asyncio
    async def test_start_game_rooms_update_status_is_in_game(self, rm):
        """Regression: rooms_update after handle_start_game must carry status == 'in_game'."""
        lobby_ws = make_ws()
        await rm.register_lobby_connection("lobby-1", lobby_ws)
        for pid, name in [("p1", "Alice"), ("p2", "Bob")]:
            await rm.join_room("room-1", pid, make_ws())
            await rm.handle_join_lobby("room-1", pid, name)
        lobby_ws.send_json.reset_mock()
        await rm.handle_start_game("room-1")
        calls = [c[0][0] for c in lobby_ws.send_json.call_args_list]
        rooms_updates = [c for c in calls if c.get("type") == "rooms_update"]
        assert rooms_updates, "No rooms_update broadcast to lobby after handle_start_game"
        last = rooms_updates[-1]
        room_1 = next(r for r in last["rooms"] if r["room_id"] == "room-1")
        assert room_1["status"] == "in_game", (
            f"Expected 'in_game' but got '{room_1['status']}'"
        )

    @pytest.mark.asyncio
    async def test_start_game_nonexistent_room_fails(self, rm):
        ok, err = await rm.handle_start_game("room-99")
        assert ok is False

    @pytest.mark.asyncio
    async def test_start_game_already_in_game_fails(self, rm):
        for pid, name in [("p1", "Alice"), ("p2", "Bob")]:
            await rm.join_room("room-1", pid, make_ws())
            await rm.handle_join_lobby("room-1", pid, name)
        await rm.handle_start_game("room-1")
        ok, err = await rm.handle_start_game("room-1")
        assert ok is False


# ---------------------------------------------------------------------------
# handle_end_game
# ---------------------------------------------------------------------------

class TestHandleEndGame:
    @pytest.mark.asyncio
    async def test_end_game_resets_status_to_empty(self, rm):
        for pid, name in [("p1", "Alice"), ("p2", "Bob")]:
            await rm.join_room("room-1", pid, make_ws())
            await rm.handle_join_lobby("room-1", pid, name)
        await rm.handle_start_game("room-1")
        ok = await rm.handle_end_game("room-1")
        assert ok is True
        assert rm.rooms["room-1"].status == RoomStatus.EMPTY

    @pytest.mark.asyncio
    async def test_end_game_clears_lobby_players(self, rm):
        for pid, name in [("p1", "Alice"), ("p2", "Bob")]:
            await rm.join_room("room-1", pid, make_ws())
            await rm.handle_join_lobby("room-1", pid, name)
        await rm.handle_start_game("room-1")
        await rm.handle_end_game("room-1")
        assert rm.rooms["room-1"].lobby_players == []

    @pytest.mark.asyncio
    async def test_end_game_broadcasts_lobby_reset_to_all_room_clients(self, rm):
        """Regression: handle_end_game must send lobby_reset to every connected
        room client so GameRoom.jsx navigates all non-initiating players back."""
        ws1, ws2 = make_ws(), make_ws()
        for ws, pid, name in [(ws1, "p1", "Alice"), (ws2, "p2", "Bob")]:
            await rm.join_room("room-1", pid, ws)
            await rm.handle_join_lobby("room-1", pid, name)
        await rm.handle_start_game("room-1")
        ws1.send_json.reset_mock()
        ws2.send_json.reset_mock()
        await rm.handle_end_game("room-1")
        for ws in (ws1, ws2):
            calls = [c[0][0] for c in ws.send_json.call_args_list]
            assert any(c.get("type") == "lobby_reset" for c in calls), (
                "lobby_reset not sent to a room client"
            )

    @pytest.mark.asyncio
    async def test_end_game_broadcasts_rooms_update_to_lobby(self, rm):
        lobby_ws = make_ws()
        await rm.register_lobby_connection("lobby-1", lobby_ws)
        for pid, name in [("p1", "Alice"), ("p2", "Bob")]:
            await rm.join_room("room-1", pid, make_ws())
            await rm.handle_join_lobby("room-1", pid, name)
        await rm.handle_start_game("room-1")
        lobby_ws.send_json.reset_mock()
        await rm.handle_end_game("room-1")
        calls = [c[0][0] for c in lobby_ws.send_json.call_args_list]
        assert any(c.get("type") == "rooms_update" for c in calls)

    @pytest.mark.asyncio
    async def test_end_game_rooms_update_status_is_empty(self, rm):
        """Regression: rooms_update after handle_end_game must carry status == 'empty'."""
        lobby_ws = make_ws()
        await rm.register_lobby_connection("lobby-1", lobby_ws)
        for pid, name in [("p1", "Alice"), ("p2", "Bob")]:
            await rm.join_room("room-1", pid, make_ws())
            await rm.handle_join_lobby("room-1", pid, name)
        await rm.handle_start_game("room-1")
        lobby_ws.send_json.reset_mock()
        await rm.handle_end_game("room-1")
        calls = [c[0][0] for c in lobby_ws.send_json.call_args_list]
        rooms_updates = [c for c in calls if c.get("type") == "rooms_update"]
        assert rooms_updates, "No rooms_update broadcast to lobby after handle_end_game"
        last = rooms_updates[-1]
        room_1 = next(r for r in last["rooms"] if r["room_id"] == "room-1")
        assert room_1["status"] == "empty", (
            f"Expected 'empty' but got '{room_1['status']}'"
        )

    @pytest.mark.asyncio
    async def test_end_game_room_is_joinable_again(self, rm):
        for pid, name in [("p1", "Alice"), ("p2", "Bob")]:
            await rm.join_room("room-1", pid, make_ws())
            await rm.handle_join_lobby("room-1", pid, name)
        await rm.handle_start_game("room-1")
        await rm.handle_end_game("room-1")
        ok, _ = await rm.join_room("room-1", "newcomer", make_ws())
        assert ok is True

    @pytest.mark.asyncio
    async def test_end_game_nonexistent_room_returns_false(self, rm):
        result = await rm.handle_end_game("room-99")
        assert result is False


# ---------------------------------------------------------------------------
# IN_GAME reconnect (Bug 2 & 3 regression)
# ---------------------------------------------------------------------------

class TestInGameReconnect:
    @pytest.mark.asyncio
    async def test_lobby_player_can_rejoin_in_game_room(self, rm):
        """A player in lobby_players must be allowed to reconnect to an IN_GAME
        room so GameRoom.jsx can open a new WebSocket after PlayerLobby unmounts."""
        ws1, ws2 = make_ws(), make_ws()
        for ws, pid, name in [(ws1, "p1", "Alice"), (ws2, "p2", "Bob")]:
            await rm.join_room("room-1", pid, ws)
            await rm.handle_join_lobby("room-1", pid, name)
        await rm.handle_start_game("room-1")

        # p1's PlayerLobby has unmounted; GameRoom opens a new WebSocket
        new_ws = make_ws()
        ok, err = await rm.join_room("room-1", "p1", new_ws)
        assert ok is True, f"Reconnect rejected: {err}"
        assert rm.room_connections["room-1"]["p1"] is new_ws

    @pytest.mark.asyncio
    async def test_player_not_in_game_cannot_join_in_game_room(self, rm):
        """A stranger must still be rejected while a game is in progress."""
        ws1, ws2 = make_ws(), make_ws()
        for ws, pid, name in [(ws1, "p1", "Alice"), (ws2, "p2", "Bob")]:
            await rm.join_room("room-1", pid, ws)
            await rm.handle_join_lobby("room-1", pid, name)
        await rm.handle_start_game("room-1")

        ok, err = await rm.join_room("room-1", "stranger", make_ws())
        assert ok is False
        assert "in progress" in err.lower()

    @pytest.mark.asyncio
    async def test_leave_room_in_game_preserves_game_state(self, rm):
        """leave_room during IN_GAME must not touch player_ids, lobby_players,
        player_count, or status — handle_end_game owns that cleanup."""
        ws1, ws2 = make_ws(), make_ws()
        for ws, pid, name in [(ws1, "p1", "Alice"), (ws2, "p2", "Bob")]:
            await rm.join_room("room-1", pid, ws)
            await rm.handle_join_lobby("room-1", pid, name)
        await rm.handle_start_game("room-1")

        player_ids_before = list(rm.rooms["room-1"].player_ids)
        lobby_players_before = list(rm.rooms["room-1"].lobby_players)

        await rm.leave_room("room-1", "p1")

        room = rm.rooms["room-1"]
        # Status must remain IN_GAME
        assert room.status == RoomStatus.IN_GAME
        # Game state must be untouched
        assert room.player_ids == player_ids_before
        assert room.player_count == len(player_ids_before)
        assert [p.id for p in room.lobby_players] == [p.id for p in lobby_players_before]
        # WebSocket connection must be gone
        assert "p1" not in rm.room_connections["room-1"]

        # Even when ALL connections drop, status stays IN_GAME
        await rm.leave_room("room-1", "p2")
        assert rm.rooms["room-1"].status == RoomStatus.IN_GAME

    @pytest.mark.asyncio
    async def test_leave_room_in_game_does_not_broadcast_lobby_update(self, rm):
        """Disconnecting while IN_GAME must not push a lobby_update with an
        empty player list to the remaining GameRoom clients."""
        ws1, ws2 = make_ws(), make_ws()
        for ws, pid, name in [(ws1, "p1", "Alice"), (ws2, "p2", "Bob")]:
            await rm.join_room("room-1", pid, ws)
            await rm.handle_join_lobby("room-1", pid, name)
        await rm.handle_start_game("room-1")
        ws2.send_json.reset_mock()

        await rm.leave_room("room-1", "p1")

        calls = [c[0][0] for c in ws2.send_json.call_args_list]
        assert not any(c.get("type") == "lobby_update" for c in calls), (
            "lobby_update must not be sent to GameRoom clients on disconnect"
        )
