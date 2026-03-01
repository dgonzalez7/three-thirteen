import React, { useState, useEffect, useRef, useCallback } from 'react';

const WS_ROOM_BASE = `${window.location.protocol === 'https:' ? 'wss' : 'ws'}://${window.location.host}/ws/room`;

const s = {
  page: {
    minHeight: '100vh',
    background: 'linear-gradient(135deg, #0f172a 0%, #1e1b4b 50%, #0f172a 100%)',
    display: 'flex',
    flexDirection: 'column',
    alignItems: 'center',
    padding: '2rem 1rem 3rem',
    fontFamily: "'Segoe UI', system-ui, sans-serif",
    color: '#e2e8f0',
  },
  header: {
    width: '100%',
    maxWidth: '600px',
    display: 'flex',
    alignItems: 'center',
    justifyContent: 'space-between',
    marginBottom: '2rem',
    flexWrap: 'wrap',
    gap: '0.75rem',
  },
  headerLeft: { display: 'flex', flexDirection: 'column', gap: '0.2rem' },
  roomLabel: {
    fontSize: '0.72rem', fontWeight: 700, color: '#64748b',
    textTransform: 'uppercase', letterSpacing: '0.12em',
  },
  roomName: {
    fontSize: '1.6rem', fontWeight: 800,
    background: 'linear-gradient(90deg, #818cf8, #c084fc)',
    WebkitBackgroundClip: 'text',
    WebkitTextFillColor: 'transparent',
    backgroundClip: 'text',
    margin: 0,
  },
  gameLabel: { fontSize: '0.82rem', color: '#94a3b8', marginTop: '0.1rem' },
  connBadge: (ok) => ({
    display: 'inline-flex', alignItems: 'center', gap: '0.4rem',
    padding: '0.3rem 0.85rem', borderRadius: '20px',
    fontSize: '0.78rem', fontWeight: 600,
    background: ok ? 'rgba(34,197,94,0.15)' : 'rgba(239,68,68,0.15)',
    color: ok ? '#86efac' : '#fca5a5',
    border: `1px solid ${ok ? 'rgba(34,197,94,0.3)' : 'rgba(239,68,68,0.3)'}`,
    whiteSpace: 'nowrap',
  }),
  dot: (ok) => ({
    width: '7px', height: '7px', borderRadius: '50%',
    background: ok ? '#22c55e' : '#ef4444',
    boxShadow: ok ? '0 0 5px #22c55e' : 'none',
  }),
  card: {
    background: 'rgba(255,255,255,0.05)',
    border: '1px solid rgba(255,255,255,0.12)',
    borderRadius: '20px',
    padding: '2rem',
    width: '100%',
    maxWidth: '600px',
    display: 'flex',
    flexDirection: 'column',
    gap: '1.5rem',
    boxShadow: '0 16px 48px rgba(0,0,0,0.4)',
  },
  sectionLabel: {
    fontSize: '0.72rem', fontWeight: 700, color: '#64748b',
    textTransform: 'uppercase', letterSpacing: '0.12em',
    marginBottom: '0.6rem',
  },
  playerList: {
    listStyle: 'none', margin: 0, padding: 0,
    display: 'flex', flexDirection: 'column', gap: '0.4rem',
  },
  playerItem: (isYou) => ({
    padding: '0.5rem 0.85rem',
    borderRadius: '10px',
    background: isYou ? 'rgba(129,140,248,0.12)' : 'rgba(255,255,255,0.04)',
    border: `1px solid ${isYou ? 'rgba(129,140,248,0.3)' : 'rgba(255,255,255,0.07)'}`,
    fontSize: '0.9rem',
    color: isYou ? '#a5b4fc' : '#cbd5e1',
    fontWeight: isYou ? 700 : 400,
    display: 'flex', alignItems: 'center', gap: '0.5rem',
  }),
  playerNum: { color: '#475569', fontSize: '0.75rem', minWidth: '1.2rem' },
  youBadge: {
    marginLeft: 'auto',
    fontSize: '0.65rem', fontWeight: 700, color: '#818cf8',
    background: 'rgba(129,140,248,0.15)',
    padding: '0.1rem 0.45rem', borderRadius: '4px',
    textTransform: 'uppercase', letterSpacing: '0.06em',
  },
  emptySlot: {
    padding: '0.5rem 0.85rem',
    borderRadius: '10px',
    background: 'rgba(255,255,255,0.02)',
    border: '1px dashed rgba(255,255,255,0.07)',
    fontSize: '0.82rem', color: '#334155',
    fontStyle: 'italic',
  },
  divider: { height: '1px', background: 'rgba(255,255,255,0.08)' },
  label: {
    display: 'block',
    fontSize: '0.82rem', fontWeight: 600, color: '#94a3b8',
    textTransform: 'uppercase', letterSpacing: '0.08em',
    marginBottom: '0.45rem',
  },
  inputRow: { display: 'flex', gap: '0.6rem' },
  input: {
    flex: 1,
    padding: '0.75rem 1rem',
    background: 'rgba(255,255,255,0.07)',
    border: '1px solid rgba(255,255,255,0.15)',
    borderRadius: '10px',
    color: '#f1f5f9',
    fontSize: '1rem',
    outline: 'none',
    minWidth: 0,
  },
  joinBtn: (disabled) => ({
    padding: '0.75rem 1.2rem',
    background: disabled ? 'rgba(99,102,241,0.3)' : 'linear-gradient(135deg, #6366f1, #8b5cf6)',
    border: 'none',
    borderRadius: '10px',
    color: disabled ? '#94a3b8' : '#fff',
    fontWeight: 700,
    fontSize: '0.95rem',
    cursor: disabled ? 'not-allowed' : 'pointer',
    whiteSpace: 'nowrap',
    transition: 'opacity 0.15s',
  }),
  startBtn: (disabled) => ({
    width: '100%',
    padding: '0.9rem 1rem',
    background: disabled
      ? 'rgba(255,255,255,0.04)'
      : 'linear-gradient(135deg, #10b981, #059669)',
    border: disabled ? '1px solid rgba(255,255,255,0.1)' : 'none',
    borderRadius: '12px',
    color: disabled ? '#475569' : '#fff',
    fontWeight: 700,
    fontSize: '1.05rem',
    cursor: disabled ? 'not-allowed' : 'pointer',
    transition: 'all 0.15s',
  }),
  startHint: {
    textAlign: 'center', fontSize: '0.78rem', color: '#475569',
    marginTop: '-0.75rem',
  },
  backLink: {
    textAlign: 'center', fontSize: '0.82rem', color: '#64748b',
    cursor: 'pointer', textDecoration: 'underline',
  },
  error: {
    background: 'rgba(239,68,68,0.12)',
    border: '1px solid rgba(239,68,68,0.35)',
    borderRadius: '8px', padding: '0.55rem 0.9rem',
    fontSize: '0.83rem', color: '#fca5a5',
  },
  inGameBox: {
    background: 'rgba(239,68,68,0.08)',
    border: '1px solid rgba(239,68,68,0.3)',
    borderRadius: '12px', padding: '1.5rem',
    textAlign: 'center', display: 'flex', flexDirection: 'column',
    gap: '1rem',
  },
  inGameTitle: { fontSize: '1.1rem', fontWeight: 700, color: '#fca5a5', margin: 0 },
  inGameMsg: { fontSize: '0.9rem', color: '#94a3b8', margin: 0 },
};

const PlayerLobby = ({ roomId, roomName, onGameStarting, onBack }) => {
  const [isConnected, setIsConnected] = useState(false);
  const [players, setPlayers] = useState([]);
  const [myName, setMyName] = useState('');
  const [nameInput, setNameInput] = useState('');
  const [hasJoined, setHasJoined] = useState(false);
  const [roomStatus, setRoomStatus] = useState('gathering');
  const [error, setError] = useState('');

  // Stable player ID created once on mount — never changes for this session
  const playerId = useRef(crypto.randomUUID()).current;

  // WebSocket ref — never stored in state
  const wsRef = useRef(null);

  // Mirror callback props and mutable state into refs so WS closures never go stale
  // Dependency array for the WS effect is [roomId] only — these refs let us access
  // current values without reopening the socket on every parent render.
  const onGameStartingRef = useRef(onGameStarting);
  useEffect(() => { onGameStartingRef.current = onGameStarting; }, [onGameStarting]);

  const onBackRef = useRef(onBack);
  useEffect(() => { onBackRef.current = onBack; }, [onBack]);

  const myNameRef = useRef('');

  useEffect(() => {
    // Guard: if a connection already exists and is open/connecting, bail out.
    // This prevents React StrictMode's mount → unmount → remount from opening
    // two parallel connections in development.
    if (wsRef.current && wsRef.current.readyState < 2) return;

    let isMounted = true;

    const url = `${WS_ROOM_BASE}/${roomId}?player_id=${encodeURIComponent(playerId)}`;
    const ws = new WebSocket(url);
    wsRef.current = ws;

    let didConnect = false;

    ws.onopen = () => {
      if (isMounted) {
        didConnect = true;
        setIsConnected(true);
      }
    };

    ws.onclose = () => {
      if (isMounted) {
        setIsConnected(false);
        // If we never successfully connected, retry automatically.
        // This handles the case where the server rejected the connection
        // due to a race condition (e.g. StrictMode double-mount).
        if (!didConnect) {
          setTimeout(() => {
            if (isMounted) {
              wsRef.current = null;
              const retryUrl = `${WS_ROOM_BASE}/${roomId}?player_id=${encodeURIComponent(playerId)}`;
              const retryWs = new WebSocket(retryUrl);
              wsRef.current = retryWs;
              retryWs.onopen = () => { if (isMounted) { didConnect = true; setIsConnected(true); } };
              retryWs.onclose = () => { if (isMounted) setIsConnected(false); };
              retryWs.onerror = () => retryWs.close();
              retryWs.onmessage = ws.onmessage;
            }
          }, 500);
        }
      }
    };

    ws.onerror = () => {
      // Let onclose handle state; just close the socket
      ws.close();
    };

    ws.onmessage = (event) => {
      if (!isMounted) return;
      try {
        const data = JSON.parse(event.data);
        switch (data.type) {
          case 'lobby_update':
            setPlayers(data.players || []);
            setRoomStatus(data.status || 'gathering');
            break;

          case 'game_starting':
            // Rule 5: all players OTHER than the one who clicked "Start" navigate here.
            // The initiating player navigates immediately in handleStartGame below.
            onGameStartingRef.current({
              roomId,
              roomName,
              players: data.players || [],
              myPlayerId: playerId,
              myName: myNameRef.current,
            });
            break;

          case 'error':
            setError(data.message || 'An error occurred.');
            break;

          default:
            break;
        }
      } catch { /* ignore malformed messages */ }
    };

    return () => {
      isMounted = false;
      if (wsRef.current === ws) {
        ws.close(1000, 'PlayerLobby unmounted');
        wsRef.current = null;
      }
    };
    // Dependency array intentionally contains only [roomId].
    // All callback props are accessed via refs above so they never need to be
    // listed here — adding them would reopen the WS on every App re-render.
  }, [roomId]); // eslint-disable-line react-hooks/exhaustive-deps

  const handleJoin = useCallback(() => {
    const trimmed = nameInput.trim();
    if (!trimmed || !wsRef.current) return;
    wsRef.current.send(JSON.stringify({
      type: 'join_lobby',
      room_id: roomId,
      player_name: trimmed,
    }));
    myNameRef.current = trimmed;
    setMyName(trimmed);
    setHasJoined(true);
    setError('');
  }, [nameInput, roomId]);

  const handleKeyDown = (e) => { if (e.key === 'Enter') handleJoin(); };

  const handleStartGame = useCallback(() => {
    if (!wsRef.current || players.length < 2) return;
    wsRef.current.send(JSON.stringify({ type: 'start_game', room_id: roomId }));
    // Rule 5: initiating player navigates immediately — send() has already
    // queued the message. Other players navigate when game_starting arrives.
    onGameStartingRef.current({
      roomId,
      roomName,
      players,
      myPlayerId: playerId,
      myName: myNameRef.current,
    });
  }, [players, roomId, roomName, playerId]);

  const handleBack = useCallback(() => {
    // Fire and forget — server removes us from lobby_players list
    if (wsRef.current && wsRef.current.readyState === WebSocket.OPEN) {
      wsRef.current.send(JSON.stringify({ type: 'leave_lobby', room_id: roomId }));
    }
    onBackRef.current();
  }, [roomId]);

  // If the room is already in_game when we arrive (before we've joined the named list)
  const isInGame = roomStatus === 'in_game' && !hasJoined;

  const canStart = hasJoined && players.length >= 2;

  return (
    <div style={s.page}>
      <div style={s.header}>
        <div style={s.headerLeft}>
          <span style={s.roomLabel}>Room</span>
          <h2 style={s.roomName}>{roomName}</h2>
          <span style={s.gameLabel}>Game: Three Thirteen</span>
        </div>
        <div style={s.connBadge(isConnected)}>
          <span style={s.dot(isConnected)} />
          {isConnected ? 'Connected ●' : 'Connecting…'}
        </div>
      </div>

      <div style={s.card}>
        {isInGame ? (
          <div style={s.inGameBox}>
            <p style={s.inGameTitle}>🔒 Game in Progress</p>
            <p style={s.inGameMsg}>
              A game is already underway in this room.
              Please go back and choose another room.
            </p>
            <span style={s.backLink} onClick={handleBack}>← Back to rooms</span>
          </div>
        ) : (
          <>
            <div>
              <p style={s.sectionLabel}>Players waiting ({players.length})</p>
              <ul style={s.playerList}>
                {players.map((p, i) => {
                  const isYou = p.id === playerId;
                  return (
                    <li key={p.id} style={s.playerItem(isYou)}>
                      <span style={s.playerNum}>{i + 1}.</span>
                      <span>{p.name}</span>
                      {isYou && <span style={s.youBadge}>you</span>}
                    </li>
                  );
                })}
                {players.length === 0 && (
                  <li style={s.emptySlot}>No players yet — be the first!</li>
                )}
              </ul>
            </div>

            <div style={s.divider} />

            {!hasJoined ? (
              <div>
                <label style={s.label}>Your name</label>
                <div style={s.inputRow}>
                  <input
                    style={s.input}
                    type="text"
                    value={nameInput}
                    onChange={e => setNameInput(e.target.value)}
                    onKeyDown={handleKeyDown}
                    placeholder="Enter your name…"
                    maxLength={20}
                    autoFocus
                  />
                  <button
                    style={s.joinBtn(!nameInput.trim())}
                    onClick={handleJoin}
                    disabled={!nameInput.trim()}
                  >
                    Join the Group
                  </button>
                </div>
                {error && <div style={{ ...s.error, marginTop: '0.6rem' }}>{error}</div>}
              </div>
            ) : (
              <div style={{ fontSize: '0.88rem', color: '#64748b', textAlign: 'center' }}>
                Joined as <strong style={{ color: '#a5b4fc' }}>{myName}</strong>
              </div>
            )}

            <div style={s.divider} />

            <button
              style={s.startBtn(!canStart)}
              onClick={handleStartGame}
              disabled={!canStart}
            >
              🚀 Start the Game
            </button>
            {!canStart && (
              <p style={s.startHint}>
                {!hasJoined
                  ? 'Enter your name to join'
                  : `Need at least 2 players (${players.length} joined)`}
              </p>
            )}

            <span style={s.backLink} onClick={handleBack}>← Back to room list</span>
          </>
        )}
      </div>
    </div>
  );
};

export default PlayerLobby;
