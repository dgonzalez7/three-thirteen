import pytest
from unittest.mock import Mock, AsyncMock, patch
import asyncio
from fastapi import WebSocket

from game.room_manager import RoomManager
from game.state import RoomState, Player

class TestRoomManager:
    """Test cases for RoomManager"""
    
    def setup_method(self):
        """Setup test fixtures"""
        self.room_manager = RoomManager()
        self.mock_websocket = Mock(spec=WebSocket)
        self.mock_websocket.send_json = AsyncMock()
    
    @pytest.mark.asyncio
    async def test_create_room(self):
        """Test room creation"""
        # TODO: Test room creation with default settings
        # TODO: Test room creation with custom max players
        # TODO: Verify room ID generation
        room_id = await self.room_manager.create_room()
        
        assert room_id in self.room_manager.rooms
        assert room_id in self.room_manager.room_connections
        assert len(self.room_manager.rooms[room_id].max_players) == 8
    
    @pytest.mark.asyncio
    async def test_join_room(self):
        """Test joining a room"""
        # TODO: Test successful room join
        # TODO: Test joining non-existent room
        # TODO: Test duplicate player join
        # TODO: Test room capacity limits
        room_id = await self.room_manager.create_room(max_players=4)
        
        success = await self.room_manager.join_room(
            room_id, 
            "player1", 
            self.mock_websocket
        )
        
        assert success is True
        assert "player1" in self.room_manager.room_connections[room_id]
    
    @pytest.mark.asyncio
    async def test_join_nonexistent_room(self):
        """Test joining a room that doesn't exist"""
        success = await self.room_manager.join_room(
            "nonexistent",
            "player1",
            self.mock_websocket
        )
        
        assert success is False
    
    @pytest.mark.asyncio
    async def test_leave_room(self):
        """Test leaving a room"""
        # TODO: Test successful room leave
        # TODO: Test leaving non-existent room
        # TODO: Test leaving room player not in
        room_id = await self.room_manager.create_room()
        
        # First join the room
        await self.room_manager.join_room(room_id, "player1", self.mock_websocket)
        
        # Then leave
        success = await self.room_manager.leave_room(room_id, "player1")
        
        assert success is True
        assert "player1" not in self.room_manager.room_connections[room_id]
    
    @pytest.mark.asyncio
    async def test_broadcast_to_room(self):
        """Test broadcasting messages to room"""
        # TODO: Test successful broadcast
        # TODO: Test broadcast to empty room
        # TODO: Test broadcast with disconnected clients
        # TODO: Verify cleanup of disconnected players
        room_id = await self.room_manager.create_room()
        
        # Add multiple players
        mock_ws2 = Mock(spec=WebSocket)
        mock_ws2.send_json = AsyncMock()
        
        await self.room_manager.join_room(room_id, "player1", self.mock_websocket)
        await self.room_manager.join_room(room_id, "player2", mock_ws2)
        
        message = {"type": "test", "data": "hello"}
        sent_count = await self.room_manager.broadcast_to_room(room_id, message)
        
        assert sent_count == 2
        self.mock_websocket.send_json.assert_called_once_with(message)
        mock_ws2.send_json.assert_called_once_with(message)
    
    def test_get_room_state(self):
        """Test getting room state"""
        # TODO: Test getting existing room state
        # TODO: Test getting non-existent room state
        room_id = "test_room"
        self.room_manager.rooms[room_id] = RoomState(
            room_id=room_id,
            max_players=4,
            created_at="2023-01-01T00:00:00"
        )
        
        state = self.room_manager.get_room_state(room_id)
        assert state is not None
        assert state.room_id == room_id
        
        nonexistent = self.room_manager.get_room_state("nonexistent")
        assert nonexistent is None
    
    def test_get_active_rooms(self):
        """Test getting list of active rooms"""
        # TODO: Test active rooms filter
        # TODO: Test empty rooms list
        room_id1 = "room1"
        room_id2 = "room2"
        
        self.room_manager.rooms[room_id1] = RoomState(
            room_id=room_id1,
            max_players=4,
            created_at="2023-01-01T00:00:00",
            is_active=True
        )
        
        self.room_manager.rooms[room_id2] = RoomState(
            room_id=room_id2,
            max_players=4,
            created_at="2023-01-01T00:00:00",
            is_active=False
        )
        
        active_rooms = self.room_manager.get_active_rooms()
        assert len(active_rooms) == 2  # TODO: Filter by active status
    
    @pytest.mark.asyncio
    async def test_cleanup_inactive_rooms(self):
        """Test cleanup of inactive rooms"""
        # TODO: Test room inactivity detection
        # TODO: Test cleanup of old rooms
        # TODO: Test cleanup of orphaned connections
        cleaned_count = await self.room_manager.cleanup_inactive_rooms()
        assert isinstance(cleaned_count, int)

# TODO: Add integration tests with GameEngine
# TODO: Add WebSocket connection tests
# TODO: Add concurrency tests for multiple players
# TODO: Add performance tests for room management
