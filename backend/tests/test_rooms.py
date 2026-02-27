import pytest
from unittest.mock import AsyncMock, MagicMock
from fastapi import WebSocket

from game.room_manager import RoomManager, NUM_ROOMS
from game.state import RoomStatus


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
