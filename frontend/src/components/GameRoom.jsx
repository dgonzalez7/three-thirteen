import React, { useState, useEffect, useRef, useCallback } from 'react';
import './GameRoom.css';

// TODO: Add card rendering components
// TODO: Add player hand display
// TODO: Add game board visualization
// TODO: Add turn indicators
// TODO: Add action buttons
// TODO: Add animations for card movements

const WS_ROOM_BASE = 'ws://localhost:8000/ws/room';

const ns = {
  overlay: {
    minHeight: '100vh',
    background: 'linear-gradient(135deg, #0f172a 0%, #1e1b4b 50%, #0f172a 100%)',
    display: 'flex',
    alignItems: 'center',
    justifyContent: 'center',
    fontFamily: "'Segoe UI', system-ui, sans-serif",
    color: '#e2e8f0',
  },
  card: {
    background: 'rgba(255,255,255,0.05)',
    border: '1px solid rgba(255,255,255,0.12)',
    borderRadius: '18px',
    padding: '2.5rem 2rem',
    width: '100%',
    maxWidth: '380px',
    display: 'flex',
    flexDirection: 'column',
    gap: '1.2rem',
    boxShadow: '0 16px 48px rgba(0,0,0,0.4)',
  },
  roomLabel: {
    fontSize: '0.75rem',
    fontWeight: 700,
    color: '#64748b',
    textTransform: 'uppercase',
    letterSpacing: '0.1em',
    marginBottom: '-0.4rem',
  },
  roomName: {
    fontSize: '1.6rem',
    fontWeight: 800,
    background: 'linear-gradient(90deg, #818cf8, #c084fc)',
    WebkitBackgroundClip: 'text',
    WebkitTextFillColor: 'transparent',
    backgroundClip: 'text',
    margin: 0,
  },
  label: {
    display: 'block',
    fontSize: '0.82rem',
    fontWeight: 600,
    color: '#94a3b8',
    textTransform: 'uppercase',
    letterSpacing: '0.08em',
    marginBottom: '0.45rem',
  },
  input: {
    width: '100%',
    boxSizing: 'border-box',
    padding: '0.75rem 1rem',
    background: 'rgba(255,255,255,0.07)',
    border: '1px solid rgba(255,255,255,0.15)',
    borderRadius: '10px',
    color: '#f1f5f9',
    fontSize: '1rem',
    outline: 'none',
  },
  btn: (disabled) => ({
    padding: '0.75rem 1rem',
    background: disabled
      ? 'rgba(99,102,241,0.3)'
      : 'linear-gradient(135deg, #6366f1, #8b5cf6)',
    border: 'none',
    borderRadius: '10px',
    color: disabled ? '#94a3b8' : '#fff',
    fontWeight: 700,
    fontSize: '1rem',
    cursor: disabled ? 'not-allowed' : 'pointer',
    transition: 'opacity 0.15s',
  }),
  backLink: {
    fontSize: '0.82rem',
    color: '#64748b',
    textAlign: 'center',
    cursor: 'pointer',
    textDecoration: 'underline',
  },
  error: {
    background: 'rgba(239,68,68,0.12)',
    border: '1px solid rgba(239,68,68,0.35)',
    borderRadius: '8px',
    padding: '0.55rem 0.9rem',
    fontSize: '0.83rem',
    color: '#fca5a5',
  },
};

const NameEntryScreen = ({ roomId, roomName, onConnected, onBack }) => {
  const [name, setName] = useState('');
  const [connecting, setConnecting] = useState(false);
  const [error, setError] = useState('');

  const handleJoin = useCallback(() => {
    const trimmed = name.trim();
    if (!trimmed) return;

    setConnecting(true);
    setError('');

    const playerId = `${trimmed}-${Date.now()}`;
    const url = `${WS_ROOM_BASE}/${roomId}?player_id=${encodeURIComponent(playerId)}`;
    const ws = new WebSocket(url);

    ws.onopen = () => {
      setConnecting(false);
      onConnected(ws, trimmed, playerId);
    };

    ws.onmessage = (e) => {
      try {
        const data = JSON.parse(e.data);
        if (data.type === 'error') {
          setError(data.message || 'Could not join room.');
          setConnecting(false);
          ws.close();
        }
      } catch { /* ignore */ }
    };

    ws.onerror = () => {
      setError('Could not connect to the game server.');
      setConnecting(false);
    };
  }, [name, roomId, onConnected]);

  const handleKeyDown = (e) => { if (e.key === 'Enter') handleJoin(); };

  return (
    <div style={ns.overlay}>
      <div style={ns.card}>
        <div>
          <p style={ns.roomLabel}>You are entering</p>
          <h2 style={ns.roomName}>{roomName}</h2>
        </div>

        <div>
          <label style={ns.label}>Your display name</label>
          <input
            style={ns.input}
            type="text"
            value={name}
            onChange={e => setName(e.target.value)}
            onKeyDown={handleKeyDown}
            placeholder="Enter your name…"
            maxLength={20}
            autoFocus
            disabled={connecting}
          />
        </div>

        {error && <div style={ns.error}>{error}</div>}

        <button
          style={ns.btn(!name.trim() || connecting)}
          onClick={handleJoin}
          disabled={!name.trim() || connecting}
        >
          {connecting ? 'Connecting…' : 'Join Room'}
        </button>

        <span style={ns.backLink} onClick={onBack}>← Back to room list</span>
      </div>
    </div>
  );
};

const GameRoom = ({ roomId, roomName, gameState, onLeaveRoom }) => {
  const [playerName, setPlayerName] = useState(null);
  const [isConnected, setIsConnected] = useState(false);
  const wsRef = useRef(null);
  const [selectedCards, setSelectedCards] = useState([]);
  const [currentAction, setCurrentAction] = useState(null);

  const handleConnected = useCallback((ws, name, playerId) => {
    wsRef.current = ws;
    setPlayerName(name);
    setIsConnected(true);

    ws.onclose = () => setIsConnected(false);
    ws.onerror = () => setIsConnected(false);
    // onmessage for game events is handled at App level via gameState prop
  }, []);

  useEffect(() => {
    return () => wsRef.current?.close(1000, 'GameRoom unmounted');
  }, []);

  const sendMessage = useCallback((message) => {
    if (wsRef.current?.readyState === WebSocket.OPEN) {
      wsRef.current.send(JSON.stringify(message));
    }
  }, []);

  useEffect(() => {
    // TODO: Initialize game room state
    // TODO: Set up keyboard shortcuts
    // TODO: Add sound effects
  }, [playerName]);

  // Show name-entry screen until the player has connected
  if (!playerName) {
    return (
      <NameEntryScreen
        roomId={roomId}
        roomName={roomName}
        onConnected={handleConnected}
        onBack={onLeaveRoom}
      />
    );
  }

  const handleCardSelect = (cardId) => {
    // TODO: Implement card selection logic
    // TODO: Handle multiple selection
    // TODO: Validate selection
    setSelectedCards(prev => 
      prev.includes(cardId) 
        ? prev.filter(id => id !== cardId)
        : [...prev, cardId]
    );
  };

  const handleDrawCard = () => {
    // TODO: Implement draw card action
    // TODO: Validate turn
    // TODO: Send action to server
    sendMessage({
      type: 'player_action',
      action: 'draw_card',
      player_name: playerName
    });
  };

  const handlePlayCards = () => {
    // TODO: Implement card playing logic
    // TODO: Validate play
    // TODO: Send play to server
    if (selectedCards.length === 0) return;

    sendMessage({
      type: 'player_action',
      action: 'play_cards',
      cards: selectedCards,
      player_name: playerName
    });
    
    setSelectedCards([]);
  };

  const handleDiscardCard = () => {
    // TODO: Implement discard logic
    // TODO: Validate discard
    // TODO: Send discard to server
    if (selectedCards.length !== 1) return;

    sendMessage({
      type: 'player_action',
      action: 'discard_card',
      card: selectedCards[0],
      player_name: playerName
    });
    
    setSelectedCards([]);
  };

  const renderPlayerHand = () => {
    // TODO: Implement player hand rendering
    // TODO: Add card components
    // TODO: Add selection indicators
    const currentPlayer = gameState?.players?.find(p => p.name === playerName);
    
    if (!currentPlayer) {
      return <div>Loading your hand...</div>;
    }

    return (
      <div className="player-hand">
        <h3>Your Hand</h3>
        <div className="cards-container">
          {/* TODO: Render actual card components */}
          {currentPlayer.hand?.map((card, index) => (
            <div 
              key={index}
              className={`card ${selectedCards.includes(index) ? 'selected' : ''}`}
              onClick={() => handleCardSelect(index)}
            >
              {/* TODO: Add card face rendering */}
              <div className="card-back">
                🂠
              </div>
            </div>
          ))}
        </div>
      </div>
    );
  };

  const renderGameBoard = () => {
    // TODO: Implement game board rendering
    // TODO: Add discard pile
    // TODO: Add deck display
    // TODO: Add other players' hands
    return (
      <div className="game-board">
        <div className="deck-area">
          <h3>Deck</h3>
          <div className="deck">
            {/* TODO: Show deck count */}
            <div className="card-back">🂠</div>
          </div>
        </div>
        
        <div className="discard-area">
          <h3>Discard Pile</h3>
          <div className="discard-pile">
            {/* TODO: Show top discard card */}
            <div className="card-back">🂠</div>
          </div>
        </div>
        
        <div className="other-players">
          <h3>Other Players</h3>
          {/* TODO: Render other players */}
          {gameState?.players?.filter(p => p.name !== playerName).map(player => (
            <div key={player.id} className="other-player">
              <span>{player.name}</span>
              <span>Cards: {player.hand?.length || 0}</span>
            </div>
          ))}
        </div>
      </div>
    );
  };

  const renderActionButtons = () => {
    // TODO: Implement action buttons
    // TODO: Disable based on game state
    // TODO: Add loading states
    return (
      <div className="action-buttons">
        <button onClick={handleDrawCard} className="action-button">
          Draw Card
        </button>
        <button 
          onClick={handlePlayCards} 
          className="action-button"
          disabled={selectedCards.length === 0}
        >
          Play Cards ({selectedCards.length})
        </button>
        <button 
          onClick={handleDiscardCard} 
          className="action-button"
          disabled={selectedCards.length !== 1}
        >
          Discard Card
        </button>
      </div>
    );
  };

  return (
    <div className="game-room">
      <div className="game-header">
        <h2>Game Room: {roomName}</h2>
        <div className="game-info">
          <span>Round: {gameState?.round_number || 1}</span>
          <span>Phase: {gameState?.phase}</span>
        </div>
        <button onClick={onLeaveRoom} className="leave-button">
          Leave Room
        </button>
      </div>

      <div className="game-content">
        {renderGameBoard()}
        {renderPlayerHand()}
        {renderActionButtons()}
      </div>

      {/* TODO: Add turn indicator */}
      {/* TODO: Add score display */}
      {/* TODO: Add chat component */}
    </div>
  );
};

export default GameRoom;
