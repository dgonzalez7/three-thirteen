from typing import Dict, List, Optional, Set
from fastapi import WebSocket
import asyncio
import uuid
from datetime import datetime

from .state import RoomState, GameState, Player
from .events import EventBus, GameEvent

class RoomManager:
    """Manages game rooms and player connections"""
    
    def __init__(self):
        self.rooms: Dict[str, RoomState] = {}
        self.room_connections: Dict[str, Dict[str, WebSocket]] = {}
        self.event_bus = EventBus()
        
        # TODO: Initialize room cleanup task
        # TODO: Add room capacity limits
        # TODO: Add connection monitoring
    
    async def create_room(self, max_players: int = 8) -> str:
        """Create a new game room"""
        room_id = str(uuid.uuid4())[:8]
        
        room_state = RoomState(
            room_id=room_id,
            max_players=max_players,
            created_at=datetime.utcnow().isoformat()
        )
        
        self.rooms[room_id] = room_state
        self.room_connections[room_id] = {}
        
        # TODO: Emit room created event
        # TODO: Start room cleanup timer
        
        return room_id
    
    async def join_room(self, room_id: str, player_id: str, websocket: WebSocket) -> bool:
        """Join a player to a room"""
        if room_id not in self.rooms:
            return False
        
        room = self.rooms[room_id]
        
        # TODO: Check room capacity
        # TODO: Check if player already in room
        # TODO: Validate player state
        
        # Add WebSocket connection
        self.room_connections[room_id][player_id] = websocket
        
        # TODO: Add player to game state
        # TODO: Broadcast player joined event
        # TODO: Send current room state to new player
        
        return True
    
    async def leave_room(self, room_id: str, player_id: str) -> bool:
        """Remove a player from a room"""
        if room_id not in self.rooms or room_id not in self.room_connections:
            return False
        
        # Remove WebSocket connection
        if player_id in self.room_connections[room_id]:
            del self.room_connections[room_id][player_id]
        
        # TODO: Remove player from game state
        # TODO: Handle game state updates for remaining players
        # TODO: Clean up empty rooms
        
        return True
    
    async def broadcast_to_room(self, room_id: str, message: dict) -> int:
        """Broadcast message to all players in a room"""
        if room_id not in self.room_connections:
            return 0
        
        sent_count = 0
        disconnected_players = []
        
        for player_id, websocket in self.room_connections[room_id].items():
            try:
                await websocket.send_json(message)
                sent_count += 1
            except Exception as e:
                # TODO: Log disconnection error
                disconnected_players.append(player_id)
        
        # Clean up disconnected players
        for player_id in disconnected_players:
            await self.leave_room(room_id, player_id)
        
        return sent_count
    
    def get_room_state(self, room_id: str) -> Optional[RoomState]:
        """Get current state of a room"""
        return self.rooms.get(room_id)
    
    def get_active_rooms(self) -> List[RoomState]:
        """Get list of all active rooms"""
        # TODO: Filter by active status
        return list(self.rooms.values())
    
    async def cleanup_inactive_rooms(self) -> int:
        """Remove inactive rooms and connections"""
        cleaned_count = 0
        
        # TODO: Implement room inactivity detection
        # TODO: Remove rooms that have been inactive too long
        # TODO: Clean up orphaned connections
        
        return cleaned_count
