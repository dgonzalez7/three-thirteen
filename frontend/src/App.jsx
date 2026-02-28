import React, { useState, useCallback } from 'react';
import Lobby from './components/Lobby';
import PlayerLobby from './components/PlayerLobby';
import GameRoom from './components/GameRoom';

// TODO: Add proper error boundaries
// TODO: Add routing for different game phases

function App() {
  // Phases: 'lobby' | 'player_lobby' | 'game_room'
  const [phase, setPhase] = useState('lobby');
  // { roomId, roomName } — set when a room is selected in the main lobby
  const [selectedRoom, setSelectedRoom] = useState(null);
  // { roomId, roomName, players, myPlayerId, myName } — set when game starts
  const [gameContext, setGameContext] = useState(null);

  const handleSelectRoom = useCallback((roomId) => {
    const roomNumber = roomId.split('-')[1];
    const roomName = `Room ${roomNumber}`;
    setSelectedRoom({ roomId, roomName });
    setPhase('player_lobby');
  }, []);

  const handleGameStarting = useCallback((context) => {
    // context = { roomId, roomName, players, myPlayerId, myName }
    setGameContext(context);
    setPhase('game_room');
  }, []);

  const handleBackToLobby = useCallback(() => {
    setGameContext(null);
    setSelectedRoom(null);
    setPhase('lobby');
  }, []);

  switch (phase) {
    case 'lobby':
      return <Lobby onSelectRoom={handleSelectRoom} />;

    case 'player_lobby':
      return (
        <PlayerLobby
          roomId={selectedRoom.roomId}
          roomName={selectedRoom.roomName}
          onGameStarting={handleGameStarting}
          onBack={handleBackToLobby}
        />
      );

    case 'game_room':
      return (
        <GameRoom
          roomId={gameContext.roomId}
          roomName={gameContext.roomName}
          players={gameContext.players}
          myPlayerId={gameContext.myPlayerId}
          myName={gameContext.myName}
          onBackToLobby={handleBackToLobby}
        />
      );

    default:
      return <Lobby onSelectRoom={handleSelectRoom} />;
  }
}

export default App;
