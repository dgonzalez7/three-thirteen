import React, { useState, useEffect, useRef, useCallback, useMemo } from 'react';

const WS_ROOM_BASE = 'ws://localhost:8000/ws/room';

// ---------------------------------------------------------------------------
// Rank / suit display helpers
// ---------------------------------------------------------------------------
const RANK_LABEL = {
  ace: 'A', two: '2', three: '3', four: '4', five: '5', six: '6',
  seven: '7', eight: '8', nine: '9', ten: '10', jack: 'J', queen: 'Q', king: 'K',
};
const SUIT_SYMBOL = { hearts: '♥', diamonds: '♦', clubs: '♣', spades: '♠' };
const SUIT_COLOR = { hearts: '#f87171', diamonds: '#f87171', clubs: '#e2e8f0', spades: '#e2e8f0' };
const WILD_LABEL = { 3: '3s', 4: '4s', 5: '5s', 6: '6s', 7: '7s', 8: '8s', 9: '9s', 10: '10s', jack: 'Jacks', queen: 'Queens', king: 'Kings' };
const ROUND_WILD_NAME = {
  three: '3s', four: '4s', five: '5s', six: '6s', seven: '7s', eight: '8s',
  nine: '9s', ten: '10s', jack: 'Jacks', queen: 'Queens', king: 'Kings',
};

function cardLabel(card) {
  return `${RANK_LABEL[card.rank]}${SUIT_SYMBOL[card.suit]}`;
}

// ---------------------------------------------------------------------------
// Styles
// ---------------------------------------------------------------------------
const s = {
  page: {
    minHeight: '100vh',
    background: 'linear-gradient(135deg, #0f172a 0%, #1e1b4b 50%, #0f172a 100%)',
    display: 'flex',
    flexDirection: 'column',
    alignItems: 'center',
    padding: '1rem',
    fontFamily: "'Segoe UI', system-ui, sans-serif",
    color: '#e2e8f0',
    gap: '0.75rem',
  },
  topBar: {
    width: '100%', maxWidth: '900px',
    display: 'flex', alignItems: 'center', justifyContent: 'space-between',
    gap: '0.5rem', flexWrap: 'wrap',
  },
  roundBadge: {
    background: 'rgba(129,140,248,0.18)',
    border: '1px solid rgba(129,140,248,0.35)',
    borderRadius: '10px', padding: '0.4rem 0.9rem',
    fontSize: '0.85rem', fontWeight: 700, color: '#a5b4fc',
  },
  wildBadge: {
    background: 'rgba(251,191,36,0.15)',
    border: '1px solid rgba(251,191,36,0.35)',
    borderRadius: '10px', padding: '0.4rem 0.9rem',
    fontSize: '0.85rem', fontWeight: 700, color: '#fcd34d',
  },
  connBadge: (ok) => ({
    display: 'inline-flex', alignItems: 'center', gap: '0.4rem',
    padding: '0.3rem 0.7rem', borderRadius: '20px', fontSize: '0.75rem', fontWeight: 600,
    background: ok ? 'rgba(34,197,94,0.15)' : 'rgba(239,68,68,0.15)',
    color: ok ? '#86efac' : '#fca5a5',
    border: `1px solid ${ok ? 'rgba(34,197,94,0.3)' : 'rgba(239,68,68,0.3)'}`,
  }),
  dot: (ok) => ({
    width: '6px', height: '6px', borderRadius: '50%',
    background: ok ? '#22c55e' : '#ef4444',
  }),
  panel: {
    width: '100%', maxWidth: '900px',
    background: 'rgba(255,255,255,0.04)',
    border: '1px solid rgba(255,255,255,0.1)',
    borderRadius: '16px', padding: '1rem 1.25rem',
  },
  sectionLabel: {
    fontSize: '0.68rem', fontWeight: 700, color: '#475569',
    textTransform: 'uppercase', letterSpacing: '0.12em', marginBottom: '0.5rem',
  },
  opponentsRow: {
    display: 'flex', flexWrap: 'wrap', gap: '0.6rem',
  },
  opponentCard: (isActive) => ({
    background: isActive ? 'rgba(129,140,248,0.15)' : 'rgba(255,255,255,0.04)',
    border: `1px solid ${isActive ? 'rgba(129,140,248,0.5)' : 'rgba(255,255,255,0.08)'}`,
    borderRadius: '10px', padding: '0.5rem 0.85rem',
    minWidth: '120px',
    display: 'flex', flexDirection: 'column', gap: '0.15rem',
  }),
  opponentName: (isActive) => ({
    fontSize: '0.88rem', fontWeight: 700,
    color: isActive ? '#a5b4fc' : '#cbd5e1',
  }),
  opponentScore: { fontSize: '0.75rem', color: '#64748b' },
  opponentCards: { fontSize: '0.72rem', color: '#475569' },
  pileArea: {
    display: 'flex', alignItems: 'center', gap: '1.25rem', flexWrap: 'wrap',
  },
  pileStack: {
    display: 'flex', flexDirection: 'column', alignItems: 'center', gap: '0.4rem',
  },
  pileLabel: { fontSize: '0.7rem', color: '#64748b', textTransform: 'uppercase', letterSpacing: '0.08em' },
  drawCard: (canDraw) => ({
    width: '60px', height: '88px',
    background: canDraw ? 'linear-gradient(135deg, #3730a3, #1e1b4b)' : 'rgba(55,48,163,0.3)',
    border: `2px solid ${canDraw ? '#6366f1' : 'rgba(99,102,241,0.3)'}`,
    borderRadius: '8px',
    display: 'flex', alignItems: 'center', justifyContent: 'center',
    cursor: canDraw ? 'pointer' : 'default',
    fontSize: '1.4rem',
    transition: 'transform 0.1s, border-color 0.15s',
    transform: canDraw ? 'scale(1)' : 'scale(0.97)',
  }),
  discardCard: (canDraw, card) => ({
    width: '60px', height: '88px',
    background: 'rgba(255,255,255,0.06)',
    border: `2px solid ${canDraw ? (card ? SUIT_COLOR[card.suit] : '#64748b') : 'rgba(100,116,139,0.3)'}`,
    borderRadius: '8px',
    display: 'flex', alignItems: 'center', justifyContent: 'center', flexDirection: 'column',
    cursor: canDraw ? 'pointer' : 'default',
    fontSize: '1rem', fontWeight: 800,
    color: card ? SUIT_COLOR[card.suit] : '#475569',
    transition: 'transform 0.1s',
    transform: canDraw ? 'scale(1)' : 'scale(0.97)',
  }),
  handArea: {
    display: 'flex', flexWrap: 'wrap', gap: '0.4rem',
  },
  handCard: (selected, isWild, canSelect) => ({
    width: '54px', height: '80px',
    background: selected
      ? 'rgba(99,102,241,0.3)'
      : isWild ? 'rgba(251,191,36,0.1)' : 'rgba(255,255,255,0.06)',
    border: `2px solid ${selected ? '#6366f1' : isWild ? '#fcd34d' : 'rgba(255,255,255,0.15)'}`,
    borderRadius: '8px',
    display: 'flex', alignItems: 'center', justifyContent: 'center', flexDirection: 'column',
    cursor: canSelect ? 'pointer' : 'default',
    fontSize: '0.82rem', fontWeight: 700,
    transition: 'transform 0.1s, border-color 0.15s',
    transform: selected ? 'translateY(-6px)' : 'none',
    userSelect: 'none',
  }),
  actionRow: {
    display: 'flex', gap: '0.6rem', flexWrap: 'wrap',
  },
  btn: (variant, disabled) => ({
    padding: '0.6rem 1.1rem',
    background: disabled
      ? 'rgba(255,255,255,0.04)'
      : variant === 'primary'
        ? 'linear-gradient(135deg, #6366f1, #8b5cf6)'
        : variant === 'danger'
          ? 'linear-gradient(135deg, #dc2626, #b91c1c)'
          : variant === 'warning'
            ? 'linear-gradient(135deg, #d97706, #b45309)'
            : 'rgba(255,255,255,0.07)',
    border: disabled ? '1px solid rgba(255,255,255,0.08)' : 'none',
    borderRadius: '8px',
    color: disabled ? '#475569' : '#fff',
    fontWeight: 700, fontSize: '0.85rem',
    cursor: disabled ? 'not-allowed' : 'pointer',
    transition: 'opacity 0.15s',
    whiteSpace: 'nowrap',
  }),
  notice: (type) => ({
    width: '100%', maxWidth: '900px',
    background: type === 'info'
      ? 'rgba(99,102,241,0.12)'
      : type === 'warn' ? 'rgba(251,191,36,0.12)' : 'rgba(239,68,68,0.12)',
    border: `1px solid ${type === 'info' ? 'rgba(99,102,241,0.4)' : type === 'warn' ? 'rgba(251,191,36,0.4)' : 'rgba(239,68,68,0.4)'}`,
    borderRadius: '10px', padding: '0.6rem 1rem',
    fontSize: '0.85rem', fontWeight: 600,
    color: type === 'info' ? '#a5b4fc' : type === 'warn' ? '#fcd34d' : '#fca5a5',
  }),
  divider: { height: '1px', background: 'rgba(255,255,255,0.08)', width: '100%', maxWidth: '900px' },
  scoringPanel: {
    width: '100%', maxWidth: '900px',
    background: 'rgba(255,255,255,0.04)',
    border: '1px solid rgba(255,255,255,0.1)',
    borderRadius: '16px', padding: '1.25rem',
    display: 'flex', flexDirection: 'column', gap: '1rem',
  },
  scoringTitle: { fontSize: '1.1rem', fontWeight: 800, color: '#a5b4fc', margin: 0 },
  scoringTable: { width: '100%', borderCollapse: 'collapse' },
  scoringTh: {
    fontSize: '0.72rem', fontWeight: 700, color: '#475569',
    textTransform: 'uppercase', letterSpacing: '0.1em',
    padding: '0.4rem 0.6rem', textAlign: 'left',
    borderBottom: '1px solid rgba(255,255,255,0.08)',
  },
  scoringTd: {
    padding: '0.45rem 0.6rem', fontSize: '0.88rem', color: '#cbd5e1',
    borderBottom: '1px solid rgba(255,255,255,0.05)',
  },
  finishedPanel: {
    width: '100%', maxWidth: '600px',
    background: 'rgba(255,255,255,0.04)',
    border: '1px solid rgba(255,255,255,0.1)',
    borderRadius: '20px', padding: '2rem',
    display: 'flex', flexDirection: 'column', gap: '1rem',
    alignItems: 'center', textAlign: 'center',
  },
  finishedTitle: { fontSize: '1.8rem', fontWeight: 800, color: '#fcd34d', margin: 0 },
  leaderRow: (rank) => ({
    display: 'flex', alignItems: 'center', gap: '1rem',
    padding: '0.6rem 1rem', borderRadius: '10px',
    background: rank === 0 ? 'rgba(251,191,36,0.12)' : 'rgba(255,255,255,0.03)',
    border: `1px solid ${rank === 0 ? 'rgba(251,191,36,0.3)' : 'rgba(255,255,255,0.07)'}`,
    width: '100%',
  }),
  leaderRank: (rank) => ({
    fontSize: '1.1rem', fontWeight: 800,
    color: rank === 0 ? '#fcd34d' : rank === 1 ? '#94a3b8' : '#92400e',
    minWidth: '2rem',
  }),
};

// ---------------------------------------------------------------------------
// Sub-components
// ---------------------------------------------------------------------------

function CardView({ card, selected, canSelect, onClick }) {
  const label = RANK_LABEL[card.rank];
  const suit = SUIT_SYMBOL[card.suit];
  const color = SUIT_COLOR[card.suit];
  return (
    <div
      style={{ ...s.handCard(selected, card.is_wild, canSelect), color }}
      onClick={canSelect ? onClick : undefined}
      title={card.is_wild ? 'Wild card' : undefined}
    >
      <span style={{ fontSize: '1.05rem' }}>{label}</span>
      <span style={{ fontSize: '0.9rem' }}>{suit}</span>
      {card.is_wild && <span style={{ fontSize: '0.55rem', color: '#fcd34d', marginTop: '2px' }}>W</span>}
    </div>
  );
}

function PlayerSeat({ player, isActive, isYou }) {
  const diamond = isActive ? ' ♦ ' : '';
  return (
    <div style={s.opponentCard(isActive)}>
      <span style={s.opponentName(isActive)}>
        {diamond}{player.name}{diamond}
      </span>
      <span style={s.opponentScore}>Score: {player.cumulative_score ?? 0}</span>
      {!isYou && (
        <span style={s.opponentCards}>
          {player.hand_count !== undefined
            ? `${player.hand_count} card${player.hand_count !== 1 ? 's' : ''}`
            : `${(player.hand || []).length} card${(player.hand || []).length !== 1 ? 's' : ''}`}
        </span>
      )}
    </div>
  );
}

// ---------------------------------------------------------------------------
// Main component
// ---------------------------------------------------------------------------

const GameRoom = ({ roomId, roomName, myPlayerId, myName, onBackToLobby }) => {
  const [isConnected, setIsConnected] = useState(false);
  const [game, setGame] = useState(null);
  const [selectedCardId, setSelectedCardId] = useState(null);
  const [goOutMode, setGoOutMode] = useState(false);
  const [wentOutMsg, setWentOutMsg] = useState(null);
  const [roundResults, setRoundResults] = useState(null);
  const [leaderboard, setLeaderboard] = useState(null);
  const [error, setError] = useState('');

  const wsRef = useRef(null);
  const onBackToLobbyRef = useRef(onBackToLobby);
  useEffect(() => { onBackToLobbyRef.current = onBackToLobby; }, [onBackToLobby]);

  // ---------------------------------------------------------------------------
  // WebSocket lifecycle
  // ---------------------------------------------------------------------------
  useEffect(() => {
    if (wsRef.current && wsRef.current.readyState < 2) return;

    let isMounted = true;
    const url = `${WS_ROOM_BASE}/${roomId}?player_id=${encodeURIComponent(myPlayerId)}`;
    const ws = new WebSocket(url);
    wsRef.current = ws;

    ws.onopen = () => { if (isMounted) setIsConnected(true); };
    ws.onclose = () => { if (isMounted) setIsConnected(false); };
    ws.onerror = () => ws.close();

    ws.onmessage = (event) => {
      if (!isMounted) return;
      try {
        const data = JSON.parse(event.data);
        switch (data.type) {
          case 'game_state':
            console.log('[game_state] phase:', data.game.phase, 'round:', data.game.round_number, 'next_round_requested:', data.game.next_round_requested);
            setGame(data.game);
            setError('');
            if (data.game.phase === 'playing' || data.game.phase === 'final_turns') {
              console.log('[game_state] clearing roundResults (phase=playing/final_turns)');
              setRoundResults(null);
            }
            break;
          case 'player_went_out':
            setWentOutMsg(`🃏 ${data.player_name} has gone out! Each remaining player gets one final turn.`);
            break;
          case 'round_over':
            console.log('[round_over] setting roundResults, round:', data.round_number);
            setRoundResults(data);
            setWentOutMsg(null);
            setSelectedCardId(null);
            setGoOutMode(false);
            break;
          case 'game_finished':
            setLeaderboard(data.leaderboard);
            setRoundResults(null);
            setWentOutMsg(null);
            break;
          case 'lobby_reset':
            onBackToLobbyRef.current();
            break;
          case 'error':
            setError(data.message || 'An error occurred.');
            // A server rejection during go-out mode returns the player to normal discard
            setGoOutMode(false);
            break;
          default:
            break;
        }
      } catch { /* ignore malformed */ }
    };

    return () => {
      isMounted = false;
      if (wsRef.current === ws) {
        ws.close(1000, 'GameRoom unmounted');
        wsRef.current = null;
      }
    };
  }, [roomId, myPlayerId]); // eslint-disable-line react-hooks/exhaustive-deps

  // ---------------------------------------------------------------------------
  // Derived state
  // ---------------------------------------------------------------------------
  const me = useMemo(() => {
    if (!game) return null;
    return game.players.find(p => p.id === myPlayerId) || null;
  }, [game, myPlayerId]);

  const isMyTurn = useMemo(() => {
    if (!game || !me) return false;
    return game.players[game.current_player_index]?.id === myPlayerId;
  }, [game, me, myPlayerId]);

  const canDraw = isMyTurn && game?.turn_phase === 'draw' &&
    (game?.phase === 'playing' || game?.phase === 'final_turns');
  const canDiscard = isMyTurn && game?.turn_phase === 'discard' &&
    (game?.phase === 'playing' || game?.phase === 'final_turns');

  const opponents = useMemo(() => {
    if (!game) return [];
    const myIdx = game.players.findIndex(p => p.id === myPlayerId);
    if (myIdx === -1) return game.players;
    const result = [];
    for (let i = 1; i < game.players.length; i++) {
      result.push(game.players[(myIdx + i) % game.players.length]);
    }
    return result;
  }, [game, myPlayerId]);

  // ---------------------------------------------------------------------------
  // Actions
  // ---------------------------------------------------------------------------
  const send = useCallback((msg) => {
    if (wsRef.current && wsRef.current.readyState === WebSocket.OPEN) {
      wsRef.current.send(JSON.stringify(msg));
    }
  }, []);

  const handleDrawFromPile = useCallback(() => {
    send({ type: 'draw_card', room_id: roomId, source: 'pile' });
  }, [send, roomId]);

  const handleDrawFromDiscard = useCallback(() => {
    send({ type: 'draw_card', room_id: roomId, source: 'discard' });
  }, [send, roomId]);

  const handleCardClick = useCallback((cardId) => {
    if (!canDiscard) return;
    if (goOutMode) {
      // In go-out mode a card click immediately attempts to go out
      send({ type: 'go_out', room_id: roomId, card_id: cardId });
      setSelectedCardId(null);
      // Stay in goOutMode — server will reject with an error or accept;
      // on rejection the error handler will clear goOutMode
    } else {
      setSelectedCardId(prev => prev === cardId ? null : cardId);
    }
  }, [canDiscard, goOutMode, send, roomId]);

  const handleDiscard = useCallback(() => {
    if (!selectedCardId || !canDiscard || goOutMode) return;
    send({ type: 'discard_card', room_id: roomId, card_id: selectedCardId });
    setSelectedCardId(null);
  }, [selectedCardId, canDiscard, goOutMode, send, roomId]);

  const handleEnterGoOutMode = useCallback(() => {
    if (!canDiscard) return;
    setGoOutMode(true);
    setSelectedCardId(null);
    setError('');
  }, [canDiscard]);

  const handleCancelGoOut = useCallback(() => {
    setGoOutMode(false);
    setSelectedCardId(null);
    setError('');
  }, []);

  const handleNextRound = useCallback(() => {
    send({ type: 'next_round', room_id: roomId });
    setRoundResults(null);
  }, [send, roomId]);

  const handleEndGame = useCallback(() => {
    send({ type: 'end_game', room_id: roomId });
    setTimeout(() => onBackToLobbyRef.current(), 500);
  }, [send, roomId]);

  // ---------------------------------------------------------------------------
  // Render: waiting for game state
  // ---------------------------------------------------------------------------
  if (!game) {
    return (
      <div style={s.page}>
        <div style={s.notice('info')}>
          {isConnected ? 'Waiting for game state…' : 'Connecting…'}
        </div>
      </div>
    );
  }

  // ---------------------------------------------------------------------------
  // Render: game finished
  // ---------------------------------------------------------------------------
  if (leaderboard) {
    return (
      <div style={s.page}>
        <div style={s.finishedPanel}>
          <div style={{ fontSize: '3rem' }}>🏆</div>
          <h2 style={s.finishedTitle}>Game Over!</h2>
          {leaderboard.map((entry, i) => (
            <div key={entry.id} style={s.leaderRow(i)}>
              <span style={s.leaderRank(i)}>{i + 1}{i === 0 ? 'st' : i === 1 ? 'nd' : i === 2 ? 'rd' : 'th'}</span>
              <span style={{ fontWeight: 700, flex: 1 }}>{entry.name}</span>
              <span style={{ color: '#94a3b8' }}>{entry.score} pts</span>
              {i === 0 && <span style={{ color: '#fcd34d', fontSize: '0.75rem', fontWeight: 700 }}>← Winner!</span>}
            </div>
          ))}
          <button style={s.btn('primary', false)} onClick={handleEndGame}>
            Back to Lobby
          </button>
        </div>
      </div>
    );
  }

  // ---------------------------------------------------------------------------
  // Render: round over / scoring
  // ---------------------------------------------------------------------------
  if (roundResults) {
    const isLast = roundResults.round_number === 11;
    return (
      <div style={s.page}>
        <div style={s.scoringPanel}>
          <h3 style={s.scoringTitle}>Round {roundResults.round_number} Results</h3>
          <table style={s.scoringTable}>
            <thead>
              <tr>
                <th style={s.scoringTh}>Player</th>
                <th style={s.scoringTh}>This Round</th>
                <th style={s.scoringTh}>Total</th>
                <th style={s.scoringTh}>Penalty Cards</th>
              </tr>
            </thead>
            <tbody>
              {roundResults.results.map(r => (
                <tr key={r.player_id}>
                  <td style={s.scoringTd}>{r.player_name}{r.player_id === myPlayerId ? ' (you)' : ''}</td>
                  <td style={{ ...s.scoringTd, color: r.round_points === 0 ? '#86efac' : '#fca5a5', fontWeight: 700 }}>
                    {r.round_points === 0 ? '0 ★' : `+${r.round_points}`}
                  </td>
                  <td style={s.scoringTd}>{r.cumulative_score}</td>
                  <td style={{ ...s.scoringTd, color: '#94a3b8', fontSize: '0.78rem' }}>
                    {r.penalty_cards.length > 0
                      ? r.penalty_cards.map(c => cardLabel(c)).join(' ')
                      : '—'}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
          <div style={s.actionRow}>
            {game.next_round_confirmed_by?.includes(myPlayerId)
              ? <span style={{ color: '#94a3b8', fontStyle: 'italic' }}>Waiting for others…</span>
              : <button style={s.btn('primary', false)} onClick={handleNextRound}>
                  {isLast ? 'See Final Scores' : `Start Round ${roundResults.round_number + 1}`}
                </button>
            }
            <button style={s.btn('ghost', false)} onClick={handleEndGame}>
              End Game
            </button>
          </div>
        </div>
      </div>
    );
  }

  // ---------------------------------------------------------------------------
  // Render: active game
  // ---------------------------------------------------------------------------
  const currentPlayerName = game.players[game.current_player_index]?.name || '';
  const topDiscard = game.discard_pile?.length > 0 ? game.discard_pile[game.discard_pile.length - 1] : null;

  return (
    <div style={s.page}>
      {/* Top bar */}
      <div style={s.topBar}>
        <div style={{ display: 'flex', gap: '0.5rem', flexWrap: 'wrap' }}>
          <span style={s.roundBadge}>Round {game.round_number} / 11</span>
          <span style={s.wildBadge}>Wild: {ROUND_WILD_NAME[game.wild_rank] || game.wild_rank}</span>
        </div>
        <div style={s.connBadge(isConnected)}>
          <span style={s.dot(isConnected)} />
          {isConnected ? 'Connected' : 'Reconnecting…'}
        </div>
      </div>

      {/* Went out notice */}
      {wentOutMsg && (
        <div style={s.notice('warn')}>{wentOutMsg}</div>
      )}

      {/* Error notice */}
      {error && (
        <div style={s.notice('error')}>{error}</div>
      )}

      {/* Opponents */}
      {opponents.length > 0 && (
        <div style={s.panel}>
          <div style={s.sectionLabel}>Other Players</div>
          <div style={s.opponentsRow}>
            {opponents.map(p => (
              <PlayerSeat
                key={p.id}
                player={p}
                isActive={game.players[game.current_player_index]?.id === p.id}
                isYou={false}
              />
            ))}
          </div>
        </div>
      )}

      {/* Piles */}
      <div style={s.panel}>
        <div style={s.sectionLabel}>
          {isMyTurn
            ? game.turn_phase === 'draw'
              ? '▶ Your turn — Draw a card'
              : goOutMode
                ? '▶ Going Out — Select the card to discard'
                : '▶ Your turn — Discard a card'
            : `${currentPlayerName}'s turn`}
        </div>
        <div style={s.pileArea}>
          {/* Draw pile */}
          <div style={s.pileStack}>
            <div
              style={s.drawCard(canDraw)}
              onClick={canDraw ? handleDrawFromPile : undefined}
              title="Draw from pile"
            >
              🂠
            </div>
            <span style={s.pileLabel}>Draw ({game.draw_pile_count ?? 0})</span>
          </div>

          {/* Discard pile */}
          <div style={s.pileStack}>
            <div
              style={s.discardCard(canDraw && topDiscard, topDiscard)}
              onClick={canDraw && topDiscard ? handleDrawFromDiscard : undefined}
              title="Draw from discard"
            >
              {topDiscard ? (
                <>
                  <span>{RANK_LABEL[topDiscard.rank]}</span>
                  <span>{SUIT_SYMBOL[topDiscard.suit]}</span>
                </>
              ) : (
                <span style={{ color: '#334155', fontSize: '0.75rem' }}>empty</span>
              )}
            </div>
            <span style={s.pileLabel}>Discard</span>
          </div>
        </div>
      </div>

      {/* My hand */}
      <div style={s.panel}>
        <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', flexWrap: 'wrap', gap: '0.4rem' }}>
          <div style={s.sectionLabel}>
            {myName || 'Your'} Hand — Score: {me?.cumulative_score ?? 0}
          </div>
          {me?.has_gone_out && (
            <span style={{ fontSize: '0.72rem', color: '#86efac', fontWeight: 700 }}>✓ Went out this round</span>
          )}
        </div>
        <div style={s.handArea}>
          {(me?.hand || []).map(card => (
            <CardView
              key={card.id}
              card={card}
              selected={selectedCardId === card.id}
              canSelect={canDiscard || goOutMode}
              onClick={() => handleCardClick(card.id)}
            />
          ))}
          {(!me?.hand || me.hand.length === 0) && (
            <span style={{ color: '#334155', fontSize: '0.85rem' }}>No cards</span>
          )}
        </div>

        {/* Action buttons */}
        {canDiscard && (
          <div style={{ ...s.actionRow, marginTop: '0.75rem' }}>
            {goOutMode ? (
              <>
                <span style={{ fontSize: '0.82rem', color: '#fcd34d', fontWeight: 700, alignSelf: 'center' }}>
                  🃏 Click a card to go out with it
                </span>
                <button style={s.btn('ghost', false)} onClick={handleCancelGoOut}>
                  Cancel
                </button>
              </>
            ) : (
              <>
                <button
                  style={s.btn('primary', !selectedCardId)}
                  disabled={!selectedCardId}
                  onClick={handleDiscard}
                >
                  Discard Selected
                </button>
                <button
                  style={s.btn('warning', false)}
                  onClick={handleEnterGoOutMode}
                  title="Server validates your remaining hand forms valid sets/runs"
                >
                  Go Out
                </button>
                {selectedCardId && (
                  <button style={s.btn('ghost', false)} onClick={() => setSelectedCardId(null)}>
                    Clear
                  </button>
                )}
              </>
            )}
          </div>
        )}
      </div>

      <div style={s.divider} />

      {/* Back button */}
      <button style={s.btn('danger', false)} onClick={handleEndGame}>
        End Game &amp; Return to Lobby
      </button>
    </div>
  );
};

export default GameRoom;
