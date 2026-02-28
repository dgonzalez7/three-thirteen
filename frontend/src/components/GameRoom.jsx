import React, { useEffect, useRef } from 'react';

const WS_ROOM_BASE = 'ws://localhost:8000/ws/room';

const s = {
  page: {
    minHeight: '100vh',
    background: 'linear-gradient(135deg, #0f172a 0%, #1e1b4b 50%, #0f172a 100%)',
    display: 'flex',
    flexDirection: 'column',
    alignItems: 'center',
    justifyContent: 'center',
    padding: '2rem 1rem',
    fontFamily: "'Segoe UI', system-ui, sans-serif",
    color: '#e2e8f0',
    gap: '1.5rem',
  },
  card: {
    background: 'rgba(255,255,255,0.05)',
    border: '1px solid rgba(255,255,255,0.12)',
    borderRadius: '20px',
    padding: '2.5rem 2rem',
    width: '100%',
    maxWidth: '520px',
    display: 'flex',
    flexDirection: 'column',
    gap: '1.5rem',
    boxShadow: '0 24px 64px rgba(0,0,0,0.5)',
    textAlign: 'center',
  },
  emoji: { fontSize: '3.5rem', lineHeight: 1 },
  title: {
    fontSize: '1.6rem',
    fontWeight: 800,
    background: 'linear-gradient(90deg, #818cf8, #c084fc, #f472b6)',
    WebkitBackgroundClip: 'text',
    WebkitTextFillColor: 'transparent',
    backgroundClip: 'text',
    margin: 0,
  },
  subtitle: { fontSize: '0.9rem', color: '#94a3b8', margin: 0 },
  divider: { height: '1px', background: 'rgba(255,255,255,0.08)' },
  sectionLabel: {
    fontSize: '0.72rem', fontWeight: 700, color: '#64748b',
    textTransform: 'uppercase', letterSpacing: '0.12em',
    textAlign: 'left', marginBottom: '0.6rem',
  },
  playerList: {
    listStyle: 'none', margin: 0, padding: 0,
    display: 'flex', flexDirection: 'column', gap: '0.4rem',
    textAlign: 'left',
  },
  playerItem: (isYou) => ({
    padding: '0.45rem 0.75rem',
    borderRadius: '8px',
    background: isYou ? 'rgba(129,140,248,0.12)' : 'rgba(255,255,255,0.04)',
    border: `1px solid ${isYou ? 'rgba(129,140,248,0.25)' : 'rgba(255,255,255,0.07)'}`,
    fontSize: '0.88rem',
    color: isYou ? '#a5b4fc' : '#cbd5e1',
    fontWeight: isYou ? 700 : 400,
    display: 'flex', alignItems: 'center', gap: '0.5rem',
  }),
  youBadge: {
    marginLeft: 'auto',
    fontSize: '0.65rem', fontWeight: 700, color: '#818cf8',
    background: 'rgba(129,140,248,0.15)',
    padding: '0.1rem 0.45rem', borderRadius: '4px',
    textTransform: 'uppercase', letterSpacing: '0.06em',
  },
  backBtn: {
    padding: '0.75rem 1rem',
    background: 'rgba(255,255,255,0.07)',
    border: '1px solid rgba(255,255,255,0.15)',
    borderRadius: '10px',
    color: '#94a3b8',
    fontWeight: 600,
    fontSize: '0.9rem',
    cursor: 'pointer',
  },
};

/**
 * GameRoom — placeholder screen shown while a game is "in progress".
 * Receives game context (roomId, roomName, players, myPlayerId, myName)
 * from PlayerLobby via App navigation state.
 *
 * Architecture rules applied:
 *   Rule 1: One WS per component, created once in useEffect([roomId, myPlayerId])
 *   Rule 2: StrictMode guard — bail out if a connection already exists
 *   Rule 3: onBackToLobby stored in a ref so the onmessage closure never goes stale
 *   Rule 4: end_game initiator navigates immediately; others navigate on lobby_reset
 */
const GameRoom = ({ roomId, roomName, players, myPlayerId, myName, onBackToLobby }) => {
  const wsRef = useRef(null);

  // Rule 3: keep callback prop in a ref — the WS effect dependency array is
  // [roomId, myPlayerId] only, so this ref is the only way the onmessage
  // closure can always call the current version of the prop.
  const onBackToLobbyRef = useRef(onBackToLobby);
  useEffect(() => { onBackToLobbyRef.current = onBackToLobby; }, [onBackToLobby]);

  useEffect(() => {
    // Rule 2: if a connection already exists and is open/connecting, bail out
    if (wsRef.current && wsRef.current.readyState < 2) return;

    let isMounted = true;

    const url = `${WS_ROOM_BASE}/${roomId}?player_id=${encodeURIComponent(myPlayerId || `spectator-${Date.now()}`)}`;
    const ws = new WebSocket(url);
    wsRef.current = ws;

    ws.onmessage = (event) => {
      if (!isMounted) return;
      try {
        const data = JSON.parse(event.data);
        // Rule 4: other players (who didn't click Back) navigate here when
        // the server broadcasts lobby_reset after processing end_game.
        if (data.type === 'lobby_reset') {
          onBackToLobbyRef.current();
        }
      } catch { /* ignore */ }
    };

    return () => {
      isMounted = false;
      if (wsRef.current === ws) {
        ws.close(1000, 'GameRoom unmounted');
        wsRef.current = null;
      }
    };
    // Dependency array intentionally contains only stable primitive values.
    // onBackToLobby is accessed via onBackToLobbyRef — adding it here would
    // reopen the WS on every App re-render.
  }, [roomId, myPlayerId]); // eslint-disable-line react-hooks/exhaustive-deps

  const handleBackToLobby = () => {
    if (wsRef.current) {
      wsRef.current.send(JSON.stringify({ type: 'end_game', room_id: roomId }));
    }
    setTimeout(() => {
      onBackToLobbyRef.current();
    }, 500);
  };

  return (
    <div style={s.page}>
      <div style={s.card}>
        <div style={s.emoji}>�</div>
        <div>
          <h2 style={s.title}>Game in Progress!</h2>
          <p style={s.subtitle}>
            Three Thirteen &mdash; {roomName} &mdash; Coming soon
          </p>
        </div>

        <div style={s.divider} />

        {players && players.length > 0 && (
          <div>
            <p style={s.sectionLabel}>Players in this game</p>
            <ul style={s.playerList}>
              {players.map((p, i) => {
                const isYou = p.id === myPlayerId;
                return (
                  <li key={p.id} style={s.playerItem(isYou)}>
                    <span style={{ color: '#475569', fontSize: '0.75rem', minWidth: '1.2rem' }}>{i + 1}.</span>
                    <span>{p.name}</span>
                    {isYou && <span style={s.youBadge}>you</span>}
                  </li>
                );
              })}
            </ul>
          </div>
        )}

        <div style={s.divider} />

        <button style={s.backBtn} onClick={handleBackToLobby}>
          ← Back to Lobby
        </button>
      </div>
    </div>
  );
};

export default GameRoom;
