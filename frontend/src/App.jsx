import React, { useState, useEffect } from 'react';
import Lobby from './components/Lobby';
import GameRoom from './components/GameRoom';
import Scoreboard from './components/Scoreboard';
import useWebSocket from './hooks/useWebSocket';
import './App.css';

// TODO: Add proper error boundaries
// TODO: Add loading states
// TODO: Add routing for different game phases
// TODO: Add responsive design

function App() {
  const [gamePhase, setGamePhase] = useState('lobby');
  const [roomId, setRoomId] = useState(null);
  const [playerName, setPlayerName] = useState('');
  const [gameState, setGameState] = useState(null);
  const [error, setError] = useState(null);

  // WebSocket connection hook
  const { 
    isConnected, 
    sendMessage, 
    lastMessage, 
    connect, 
    disconnect 
  } = useWebSocket('ws://localhost:8000');

  useEffect(() => {
    if (lastMessage) {
      // TODO: Handle incoming WebSocket messages
      // TODO: Update game state based on message type
      // TODO: Handle connection errors
      try {
        const data = JSON.parse(lastMessage.data);
        handleWebSocketMessage(data);
      } catch (err) {
        console.error('Failed to parse WebSocket message:', err);
        setError('Invalid message received from server');
      }
    }
  }, [lastMessage]);

  const handleWebSocketMessage = (data) => {
    // TODO: Implement message routing based on type
    // TODO: Update game state
    // TODO: Handle different event types
    switch (data.type) {
      case 'game_state_update':
        setGameState(data.payload);
        setGamePhase(data.payload.phase);
        break;
      case 'error':
        setError(data.message);
        break;
      default:
        console.log('Unhandled message type:', data.type);
    }
  };

  const handleJoinRoom = (roomCode, name) => {
    // TODO: Implement room joining logic
    // TODO: Validate input
    // TODO: Send join request to server
    setPlayerName(name);
    setRoomId(roomCode);
    connect(`ws://localhost:8000/ws/${roomCode}`);
  };

  const handleLeaveRoom = () => {
    // TODO: Implement room leaving logic
    // TODO: Notify server
    // TODO: Clean up state
    disconnect();
    setRoomId(null);
    setGameState(null);
    setGamePhase('lobby');
  };

  const renderCurrentPhase = () => {
    // TODO: Add phase-specific rendering
    // TODO: Add transition animations
    switch (gamePhase) {
      case 'lobby':
        return (
          <Lobby 
            onJoinRoom={handleJoinRoom}
            isConnected={isConnected}
            error={error}
          />
        );
      case 'playing':
      case 'scoring':
        return (
          <GameRoom
            gameState={gameState}
            playerName={playerName}
            sendMessage={sendMessage}
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
        return <div>Unknown game phase: {gamePhase}</div>;
    }
  };

  return (
    <div className="App">
      {/* TODO: Add header with game title and connection status */}
      {/* TODO: Add notification system for errors and messages */}
      {/* TODO: Add background theme */}
      
      {error && (
        <div className="error-message">
          {error}
          <button onClick={() => setError(null)}>Dismiss</button>
        </div>
      )}
      
      {renderCurrentPhase()}
    </div>
  );
}

export default App;
