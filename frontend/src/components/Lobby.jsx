import React, { useState } from 'react';
import './Lobby.css';

// TODO: Add room creation functionality
// TODO: Add room list display
// TODO: Add player name validation
// TODO: Add connection status indicators
// TODO: Add animations and transitions

const Lobby = ({ onJoinRoom, isConnected, error }) => {
  const [roomCode, setRoomCode] = useState('');
  const [playerName, setPlayerName] = useState('');
  const [isJoining, setIsJoining] = useState(false);

  const handleSubmit = async (e) => {
    e.preventDefault();
    
    // TODO: Validate inputs
    if (!roomCode.trim() || !playerName.trim()) {
      // TODO: Show validation error
      return;
    }

    setIsJoining(true);
    
    try {
      await onJoinRoom(roomCode.trim(), playerName.trim());
    } catch (err) {
      // TODO: Handle join error
      console.error('Failed to join room:', err);
    } finally {
      setIsJoining(false);
    }
  };

  const handleCreateRoom = () => {
    // TODO: Implement room creation
    // TODO: Generate room code
    // TODO: Auto-join created room
    console.log('Create room functionality not implemented yet');
  };

  return (
    <div className="lobby">
      <div className="lobby-container">
        <h1 className="game-title">Three-Thirteen</h1>
        <p className="game-subtitle">A Multiplayer Card Game</p>
        
        {/* TODO: Add connection status indicator */}
        <div className={`connection-status ${isConnected ? 'connected' : 'disconnected'}`}>
          {isConnected ? '🟢 Connected' : '🔴 Disconnected'}
        </div>

        {error && (
          <div className="error-banner">
            {error}
          </div>
        )}

        <div className="join-section">
          <h2>Join Game Room</h2>
          <form onSubmit={handleSubmit} className="join-form">
            <div className="form-group">
              <label htmlFor="playerName">Your Name</label>
              <input
                type="text"
                id="playerName"
                value={playerName}
                onChange={(e) => setPlayerName(e.target.value)}
                placeholder="Enter your name"
                maxLength={20}
                required
              />
            </div>
            
            <div className="form-group">
              <label htmlFor="roomCode">Room Code</label>
              <input
                type="text"
                id="roomCode"
                value={roomCode}
                onChange={(e) => setRoomCode(e.target.value.toUpperCase())}
                placeholder="Enter room code"
                maxLength={8}
                required
              />
            </div>
            
            <button 
              type="submit" 
              className="join-button"
              disabled={!isConnected || isJoining}
            >
              {isJoining ? 'Joining...' : 'Join Room'}
            </button>
          </form>
        </div>

        <div className="divider">OR</div>

        <div className="create-section">
          <h2>Create New Room</h2>
          <button 
            onClick={handleCreateRoom}
            className="create-button"
            disabled={!isConnected}
          >
            Create Room
          </button>
        </div>

        {/* TODO: Add room list component */}
        {/* TODO: Add game rules preview */}
        {/* TODO: Add player count indicator */}
      </div>
    </div>
  );
};

export default Lobby;
