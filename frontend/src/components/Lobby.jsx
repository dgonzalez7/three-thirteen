import React, { useState, useEffect, useRef, useCallback } from 'react';

const WS_LOBBY_URL = 'ws://localhost:8000/ws/lobby';

const STATUS_META = {
  empty: {
    label: 'Open',
    description: 'Waiting for players',
    color: '#22c55e',
    bg: 'rgba(34,197,94,0.08)',
    border: 'rgba(34,197,94,0.35)',
    cursor: 'pointer',
    badge: '🟢',
  },
  gathering: {
    label: 'Gathering',
    description: 'Players joining…',
    color: '#f59e0b',
    bg: 'rgba(245,158,11,0.08)',
    border: 'rgba(245,158,11,0.45)',
    cursor: 'pointer',
    badge: '🟡',
  },
  in_game: {
    label: 'In Game',
    description: 'Game underway',
    color: '#ef4444',
    bg: 'rgba(239,68,68,0.06)',
    border: 'rgba(239,68,68,0.25)',
    cursor: 'not-allowed',
    badge: '🔴',
  },
};

const SUIT_DECORS = ['♠', '♥', '♦', '♣', '♠', '♥', '♦', '♣', '♠', '♥'];

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
  banner: { textAlign: 'center', marginBottom: '2rem' },
  title: {
    fontSize: 'clamp(2.4rem, 6vw, 4rem)',
    fontWeight: 800,
    background: 'linear-gradient(90deg, #818cf8, #c084fc, #f472b6)',
    WebkitBackgroundClip: 'text',
    WebkitTextFillColor: 'transparent',
    backgroundClip: 'text',
    margin: 0,
    letterSpacing: '-0.02em',
    lineHeight: 1.1,
  },
  subtitle: {
    fontSize: '1rem',
    color: '#94a3b8',
    marginTop: '0.5rem',
    letterSpacing: '0.06em',
    textTransform: 'uppercase',
  },
  suits: { fontSize: '1.4rem', marginTop: '0.75rem', letterSpacing: '0.5rem', opacity: 0.6 },
  connBadge: (ok) => ({
    display: 'inline-flex',
    alignItems: 'center',
    gap: '0.4rem',
    padding: '0.3rem 0.85rem',
    borderRadius: '20px',
    fontSize: '0.78rem',
    fontWeight: 600,
    background: ok ? 'rgba(34,197,94,0.15)' : 'rgba(239,68,68,0.15)',
    color: ok ? '#86efac' : '#fca5a5',
    border: `1px solid ${ok ? 'rgba(34,197,94,0.3)' : 'rgba(239,68,68,0.3)'}`,
    marginBottom: '2rem',
  }),
  dot: (ok) => ({
    width: '7px', height: '7px', borderRadius: '50%',
    background: ok ? '#22c55e' : '#ef4444',
    boxShadow: ok ? '0 0 5px #22c55e' : 'none',
  }),
  heading: {
    fontSize: '0.78rem', fontWeight: 700, color: '#64748b',
    textTransform: 'uppercase', letterSpacing: '0.12em',
    marginBottom: '1rem', textAlign: 'center',
  },
  grid: {
    display: 'grid',
    gridTemplateColumns: 'repeat(auto-fill, minmax(190px, 1fr))',
    gap: '1rem',
    width: '100%',
    maxWidth: '880px',
  },
  card: (status, hov) => {
    const m = STATUS_META[status] || STATUS_META.empty;
    return {
      position: 'relative', overflow: 'hidden',
      background: hov && status !== 'in_game' ? 'rgba(255,255,255,0.07)' : m.bg,
      border: `1.5px solid ${hov && status !== 'in_game' ? m.color : m.border}`,
      borderRadius: '14px',
      padding: '1.2rem 1rem 1rem',
      cursor: m.cursor,
      transition: 'all 0.16s ease',
      transform: hov && status !== 'in_game' ? 'translateY(-3px)' : 'none',
      boxShadow: hov && status !== 'in_game'
        ? `0 8px 24px rgba(0,0,0,0.35), 0 0 0 1px ${m.color}40`
        : '0 2px 8px rgba(0,0,0,0.2)',
      opacity: status === 'in_game' ? 0.6 : 1,
      userSelect: 'none',
    };
  },
  cardName: { fontSize: '1rem', fontWeight: 700, color: '#f1f5f9', marginBottom: '0.45rem' },
  cardStatusRow: { display: 'flex', alignItems: 'center', gap: '0.35rem' },
  cardStatusLabel: (status) => ({
    fontSize: '0.8rem', fontWeight: 600,
    color: (STATUS_META[status] || STATUS_META.empty).color,
  }),
  cardCount: { fontSize: '0.75rem', color: '#94a3b8', marginTop: '0.3rem' },
  cardNote: { fontSize: '0.72rem', color: '#ef4444', marginTop: '0.35rem', fontStyle: 'italic' },
  decor: {
    fontSize: '1.1rem', opacity: 0.18,
    position: 'absolute', bottom: '0.55rem', right: '0.75rem',
    pointerEvents: 'none',
  },
  flash: {
    background: 'rgba(239,68,68,0.12)',
    border: '1px solid rgba(239,68,68,0.35)',
    borderRadius: '8px', padding: '0.55rem 1rem',
    fontSize: '0.83rem', color: '#fca5a5',
    marginBottom: '1rem', maxWidth: '880px', width: '100%', textAlign: 'center',
  },
  legend: {
    marginTop: '2.5rem', display: 'flex', gap: '1.5rem',
    flexWrap: 'wrap', justifyContent: 'center',
  },
  legendItem: { display: 'flex', alignItems: 'center', gap: '0.35rem', fontSize: '0.78rem', color: '#64748b' },
};

const RoomCard = ({ room, onSelect }) => {
  const [hov, setHov] = useState(false);
  const meta = STATUS_META[room.status] || STATUS_META.empty;
  const isInGame = room.status === 'in_game';
  const idx = parseInt(room.room_id.split('-')[1], 10) - 1;

  return (
    <div
      style={s.card(room.status, hov)}
      onMouseEnter={() => setHov(true)}
      onMouseLeave={() => setHov(false)}
      onClick={() => !isInGame && onSelect(room.room_id)}
      title={isInGame ? 'A game is already underway' : `Enter ${room.room_name}`}
    >
      <div style={s.cardName}>{room.room_name}</div>
      <div style={s.cardStatusRow}>
        <span style={{ fontSize: '0.82rem' }}>{meta.badge}</span>
        <span style={s.cardStatusLabel(room.status)}>{meta.label}</span>
      </div>
      {room.status === 'gathering' && (
        <div style={s.cardCount}>{room.player_count} / {room.max_players} players</div>
      )}
      {isInGame && <div style={s.cardNote}>Game in progress…</div>}
      <span style={s.decor}>{SUIT_DECORS[idx % 4]}</span>
    </div>
  );
};

const Lobby = ({ onSelectRoom }) => {
  const [rooms, setRooms] = useState([]);
  const [isConnected, setIsConnected] = useState(false);
  const [flash, setFlash] = useState('');

  const wsRef = useRef(null);
  const retryTimer = useRef(null);

  const connect = useCallback(() => {
    if (wsRef.current && wsRef.current.readyState < 2) return;
    try {
      const ws = new WebSocket(WS_LOBBY_URL);
      wsRef.current = ws;

      ws.onopen = () => {
        setIsConnected(true);
        if (retryTimer.current) { clearTimeout(retryTimer.current); retryTimer.current = null; }
      };
      ws.onmessage = (e) => {
        try {
          const data = JSON.parse(e.data);
          if (data.type === 'rooms_update') setRooms(data.rooms);
        } catch { /* ignore */ }
      };
      ws.onclose = () => {
        setIsConnected(false);
        retryTimer.current = setTimeout(connect, 3000);
      };
      ws.onerror = () => ws.close();
    } catch {
      retryTimer.current = setTimeout(connect, 3000);
    }
  }, []);

  useEffect(() => {
    connect();
    return () => {
      if (retryTimer.current) clearTimeout(retryTimer.current);
      wsRef.current?.close(1000, 'Lobby unmounted');
    };
  }, [connect]);

  const handleSelect = (roomId) => {
    const room = rooms.find(r => r.room_id === roomId);
    if (!room || room.status === 'in_game') {
      setFlash('That room is currently in a game. Please choose another.');
      setTimeout(() => setFlash(''), 3000);
      return;
    }
    onSelectRoom(roomId);
  };

  return (
    <div style={s.page}>
      <div style={s.banner}>
        <h1 style={s.title}>Play Three-Thirteen!</h1>
        <p style={s.subtitle}>A Real-Time Multiplayer Card Game</p>
        <div style={s.suits}>♠ ♥ ♦ ♣</div>
      </div>

      <div style={s.connBadge(isConnected)}>
        <span style={s.dot(isConnected)} />
        {isConnected ? 'Connected to server' : 'Connecting…'}
      </div>

      {flash && <div style={s.flash}>{flash}</div>}

      <div style={{ width: '100%', maxWidth: '880px' }}>
        <p style={s.heading}>Select a room to join</p>
      </div>

      {rooms.length === 0 ? (
        <div style={{ color: '#475569', fontSize: '0.9rem' }}>
          {isConnected ? 'Loading rooms…' : 'Waiting for server…'}
        </div>
      ) : (
        <div style={s.grid}>
          {rooms.map(room => (
            <RoomCard key={room.room_id} room={room} onSelect={handleSelect} />
          ))}
        </div>
      )}

      <div style={s.legend}>
        {Object.entries(STATUS_META).map(([key, m]) => (
          <div key={key} style={s.legendItem}>
            <span>{m.badge}</span>
            <span style={{ color: m.color, fontWeight: 600 }}>{m.label}</span>
            <span>— {m.description}</span>
          </div>
        ))}
      </div>
    </div>
  );
};

export default Lobby;
