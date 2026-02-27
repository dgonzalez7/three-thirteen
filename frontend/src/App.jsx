import React, { useState } from 'react';
import Lobby from './components/Lobby';
import GameRoom from './components/GameRoom';
import Scoreboard from './components/Scoreboard';

// TODO: Add proper error boundaries
// TODO: Add routing for different game phases

function App() {
  const [gamePhase, setGamePhase] = useState('lobby');
  const [selectedRoom, setSelectedRoom] = useState(null); // { roomId, roomName }
  const [gameState, setGameState] = useState(null);

  const handleSelectRoom = (roomId) => {
    // Derive a display name from the room ID (e.g. "room-3" → "Room 3")
    const roomNumber = roomId.split('-')[1];
    const roomName = `Room ${roomNumber}`;
    setSelectedRoom({ roomId, roomName });
    setGamePhase('game');
  };

  const handleLeaveRoom = () => {
    setSelectedRoom(null);
    setGameState(null);
    setGamePhase('lobby');
  };

  switch (gamePhase) {
    case 'lobby':
      return <Lobby onSelectRoom={handleSelectRoom} />;

    case 'game':
      return (
        <GameRoom
          roomId={selectedRoom?.roomId}
          roomName={selectedRoom?.roomName}
          gameState={gameState}
          onLeaveRoom={handleLeaveRoom}
        />
      );

    case 'finished':
      return (
        <Scoreboard
          gameState={gameState}
          onPlayAgain={handleLeaveRoom}
        />
      );

    default:
      return <Lobby onSelectRoom={handleSelectRoom} />;
  }
}

export default App;
