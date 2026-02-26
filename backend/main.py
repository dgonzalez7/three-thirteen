from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from typing import List
import json

from game.room_manager import RoomManager
from game.events import EventBus

# TODO: Add proper logging configuration
# TODO: Add authentication middleware
# TODO: Add rate limiting

app = FastAPI(title="Three-Thirteen Game Server")

# CORS middleware for frontend development
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Global services
room_manager = RoomManager()
event_bus = EventBus()

@app.get("/")
async def root():
    """Health check endpoint"""
    return {"status": "healthy", "message": "Three-Thirteen Game Server"}

@app.get("/rooms")
async def get_rooms():
    """Get list of available rooms"""
    # TODO: Implement room listing logic
    return {"rooms": []}

@app.post("/rooms")
async def create_room():
    """Create a new game room"""
    # TODO: Implement room creation logic
    return {"room_id": "placeholder", "status": "created"}

@app.websocket("/ws/{room_id}")
async def websocket_endpoint(websocket: WebSocket, room_id: str):
    """WebSocket endpoint for real-time game communication"""
    # TODO: Implement WebSocket connection handling
    # TODO: Implement room joining logic
    # TODO: Implement message routing
    pass

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
