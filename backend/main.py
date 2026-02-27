from fastapi import FastAPI, WebSocket, WebSocketDisconnect, Query
from fastapi.middleware.cors import CORSMiddleware
import uuid

from game.room_manager import RoomManager

app = FastAPI(title="Three-Thirteen Game Server")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Single global RoomManager instance — owns all state for v1
room_manager = RoomManager()


@app.get("/")
async def root():
    """Health check endpoint."""
    return {"status": "healthy", "message": "Three-Thirteen Game Server"}


@app.get("/rooms")
async def get_rooms():
    """Return the current state of all 10 rooms (HTTP snapshot)."""
    return {"rooms": [r.model_dump() for r in room_manager.get_all_rooms()]}


@app.websocket("/ws/lobby")
async def lobby_websocket(websocket: WebSocket):
    """Lobby WebSocket — clients connect here to receive real-time room list updates.

    The server sends a `rooms_update` event immediately on connect and again
    whenever any room's state changes.
    """
    await websocket.accept()
    connection_id = str(uuid.uuid4())

    await room_manager.register_lobby_connection(connection_id, websocket)

    try:
        # Keep the connection alive; lobby clients only receive, never send
        while True:
            await websocket.receive_text()
    except WebSocketDisconnect:
        pass
    finally:
        await room_manager.unregister_lobby_connection(connection_id)


@app.websocket("/ws/room/{room_id}")
async def room_websocket(
    websocket: WebSocket,
    room_id: str,
    player_id: str = Query(..., description="Unique player identifier"),
):
    """Game-room WebSocket — used once a player has chosen a room in the lobby.

    Query param `player_id` must be supplied by the client.
    """
    await websocket.accept()

    success, error_msg = await room_manager.join_room(room_id, player_id, websocket)

    if not success:
        await websocket.send_json({"type": "error", "message": error_msg})
        await websocket.close()
        return

    try:
        while True:
            data = await websocket.receive_json()
            # TODO: Route incoming game actions through the game engine
            _ = data
    except WebSocketDisconnect:
        pass
    finally:
        await room_manager.leave_room(room_id, player_id)


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
