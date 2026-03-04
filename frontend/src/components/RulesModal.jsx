import React, { useState } from 'react';

const s = {
  fab: {
    position: 'fixed',
    bottom: '1.5rem',
    right: '1.5rem',
    zIndex: 900,
    background: 'rgba(129,140,248,0.18)',
    border: '1px solid rgba(129,140,248,0.45)',
    borderRadius: '8px',
    color: '#a5b4fc',
    fontSize: '0.8rem',
    fontWeight: 700,
    padding: '0.45rem 0.85rem',
    cursor: 'pointer',
    letterSpacing: '0.04em',
    backdropFilter: 'blur(4px)',
    transition: 'background 0.15s, border-color 0.15s',
  },
  overlay: {
    position: 'fixed',
    inset: 0,
    zIndex: 1000,
    background: 'rgba(0,0,0,0.72)',
    display: 'flex',
    alignItems: 'center',
    justifyContent: 'center',
    padding: '1rem',
  },
  modal: {
    background: 'linear-gradient(160deg, #1e1b4b 0%, #0f172a 100%)',
    border: '1px solid rgba(129,140,248,0.35)',
    borderRadius: '14px',
    width: '100%',
    maxWidth: '640px',
    maxHeight: '80vh',
    display: 'flex',
    flexDirection: 'column',
    boxShadow: '0 24px 64px rgba(0,0,0,0.6)',
  },
  header: {
    display: 'flex',
    alignItems: 'center',
    justifyContent: 'space-between',
    padding: '1rem 1.25rem 0.75rem',
    borderBottom: '1px solid rgba(129,140,248,0.2)',
    flexShrink: 0,
  },
  title: {
    fontSize: '1rem',
    fontWeight: 700,
    color: '#a5b4fc',
    letterSpacing: '0.05em',
    fontFamily: "'Segoe UI', system-ui, sans-serif",
  },
  closeBtn: {
    background: 'none',
    border: 'none',
    color: '#94a3b8',
    fontSize: '1.3rem',
    lineHeight: 1,
    cursor: 'pointer',
    padding: '0.1rem 0.3rem',
    borderRadius: '4px',
  },
  body: {
    overflowY: 'auto',
    padding: '1.25rem',
    flexGrow: 1,
  },
  h2: {
    fontSize: '0.75rem',
    fontWeight: 700,
    letterSpacing: '0.1em',
    textTransform: 'uppercase',
    color: '#a5b4fc',
    margin: '1.5rem 0 0.5rem',
    paddingBottom: '0.3rem',
    borderBottom: '1px solid rgba(129,140,248,0.2)',
  },
  p: {
    fontSize: '0.875rem',
    lineHeight: 1.7,
    color: '#cbd5e1',
    margin: '0.4rem 0',
  },
  note: {
    fontSize: '0.8rem',
    lineHeight: 1.6,
    color: '#94a3b8',
    fontStyle: 'italic',
    background: 'rgba(129,140,248,0.08)',
    border: '1px solid rgba(129,140,248,0.2)',
    borderRadius: '6px',
    padding: '0.5rem 0.75rem',
    margin: '0.5rem 0',
  },
  ol: {
    fontSize: '0.875rem',
    lineHeight: 1.7,
    color: '#cbd5e1',
    margin: '0.4rem 0',
    paddingLeft: '1.5rem',
  },
  ul: {
    fontSize: '0.875rem',
    lineHeight: 1.7,
    color: '#cbd5e1',
    margin: '0.4rem 0',
    paddingLeft: '1.5rem',
    listStyle: 'disc',
  },
  table: {
    width: '100%',
    borderCollapse: 'collapse',
    fontSize: '0.825rem',
    margin: '0.6rem 0',
  },
  th: {
    textAlign: 'left',
    padding: '0.35rem 0.75rem',
    background: 'rgba(129,140,248,0.15)',
    color: '#a5b4fc',
    fontWeight: 700,
    fontSize: '0.75rem',
    letterSpacing: '0.06em',
    textTransform: 'uppercase',
    borderBottom: '1px solid rgba(129,140,248,0.25)',
  },
  td: {
    padding: '0.3rem 0.75rem',
    color: '#cbd5e1',
    borderBottom: '1px solid rgba(255,255,255,0.05)',
  },
  tdMono: {
    padding: '0.3rem 0.75rem',
    color: '#e2e8f0',
    fontVariantNumeric: 'tabular-nums',
    borderBottom: '1px solid rgba(255,255,255,0.05)',
  },
};

export default function RulesModal() {
  const [open, setOpen] = useState(false);

  return (
    <>
      <button style={s.fab} onClick={() => setOpen(true)}>
        📖 Rules
      </button>

      {open && (
        <div style={s.overlay} onClick={() => setOpen(false)}>
          <div style={s.modal} onClick={e => e.stopPropagation()}>
            <div style={s.header}>
              <span style={s.title}>📖 How to Play — Three Thirteen</span>
              <button style={s.closeBtn} onClick={() => setOpen(false)} aria-label="Close">✕</button>
            </div>
            <div style={s.body}>

              <h2 style={s.h2}>Overview</h2>
              <p style={s.p}>Three Thirteen is a multiplayer card game for 2–8 players, part of the Rummy family. The goal is to form sets and runs with the cards in your hand, accumulating the fewest penalty points over 11 rounds.</p>
              <p style={s.note}>These are house rules and represent a variant of the published rules.</p>

              <h2 style={s.h2}>Players</h2>
              <p style={s.p}>2 to 8 players.</p>

              <h2 style={s.h2}>Deck</h2>
              <table style={s.table}>
                <thead>
                  <tr><th style={s.th}>Players</th><th style={s.th}>Decks</th></tr>
                </thead>
                <tbody>
                  <tr><td style={s.td}>2–3</td><td style={s.tdMono}>1</td></tr>
                  <tr><td style={s.td}>4–5</td><td style={s.tdMono}>2</td></tr>
                  <tr><td style={s.td}>6–8</td><td style={s.tdMono}>3</td></tr>
                </tbody>
              </table>
              <p style={s.p}>Aces are <strong>low</strong> in runs (A-2-3 is valid; Q-K-A is not), but count <strong>high (15 points)</strong> as penalty cards.</p>

              <h2 style={s.h2}>Setup</h2>
              <p style={s.p}>The first dealer is chosen randomly. After each round, the deal passes to the left.</p>
              <table style={s.table}>
                <thead>
                  <tr><th style={s.th}>Round</th><th style={s.th}>Cards Dealt</th><th style={s.th}>Wild Card</th></tr>
                </thead>
                <tbody>
                  {[
                    [1,'3','3s'],[2,'4','4s'],[3,'5','5s'],[4,'6','6s'],
                    [5,'7','7s'],[6,'8','8s'],[7,'9','9s'],[8,'10','10s'],
                    [9,'11','Jacks'],[10,'12','Queens'],[11,'13','Kings'],
                  ].map(([r, c, w]) => (
                    <tr key={r}>
                      <td style={s.tdMono}>{r}</td>
                      <td style={s.tdMono}>{c}</td>
                      <td style={s.td}>{w}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
              <p style={s.p}>All remaining cards form the draw pile face-down. The top card is turned face-up to start the discard pile.</p>

              <h2 style={s.h2}>Wild Cards</h2>
              <p style={s.p}>In each round, one rank is wild (see table above). Wild cards may substitute for any card in a set or run. They count as their face value if left unmatched as penalty cards.</p>

              <h2 style={s.h2}>Gameplay</h2>
              <p style={s.p}>The player to the left of the dealer goes first. Play continues clockwise. On each turn:</p>
              <ol style={s.ol}>
                <li><strong>Draw</strong> — take the top face-down card from the draw pile, or the top face-up card from the discard pile.</li>
                <li><strong>Discard</strong> — place one card face-up on the discard pile (unless going out).</li>
              </ol>

              <h2 style={s.h2}>Sets and Runs</h2>
              <ul style={s.ul}>
                <li><strong>Set</strong> — three or more cards of the same rank (e.g. 7♠ 7♥ 7♦).</li>
                <li><strong>Run</strong> — three or more cards of the same suit in sequence (e.g. A♥ 2♥ 3♥).</li>
              </ul>
              <ul style={s.ul}>
                <li>Sets and runs may contain more than three cards.</li>
                <li>No card may belong to more than one combination.</li>
                <li>Any mix of sets and runs is valid.</li>
                <li>Players may <strong>not</strong> add cards to another player's combinations.</li>
              </ul>

              <h2 style={s.h2}>Going Out</h2>
              <p style={s.p}>A player may go out on their turn if, after drawing, all cards can be arranged into sets and runs with exactly one card left over to discard.</p>
              <ol style={s.ol}>
                <li>Announce going out.</li>
                <li>Lay sets and runs face-up.</li>
                <li>Discard the final card.</li>
              </ol>
              <p style={s.p}>Each remaining player then gets one final turn (clockwise). Only one player may go out per round — the first to do so. If a later player can also go out during their final turn, they score 0 points but the original going-out player remains recorded.</p>

              <h2 style={s.h2}>Scoring</h2>
              <p style={s.p}>Unmatched cards score penalty points. The player who went out scores <strong>0</strong>.</p>
              <table style={s.table}>
                <thead>
                  <tr><th style={s.th}>Card</th><th style={s.th}>Penalty Points</th></tr>
                </thead>
                <tbody>
                  <tr><td style={s.td}>Ace</td><td style={s.tdMono}>15</td></tr>
                  <tr><td style={s.td}>King / Queen / Jack</td><td style={s.tdMono}>10</td></tr>
                  <tr><td style={s.td}>2 through 10</td><td style={s.td}>Face value</td></tr>
                  <tr><td style={s.td}>Wild card</td><td style={s.td}>Face value</td></tr>
                </tbody>
              </table>

              <h2 style={s.h2}>New Round</h2>
              <p style={s.p}>After rounds 1–10, all cards are reshuffled and a new round begins with the deal passing to the left.</p>

              <h2 style={s.h2}>Winning</h2>
              <p style={s.p}>After the 11th round, the player with the <strong>lowest cumulative score</strong> wins.</p>

              <h2 style={s.h2}>Room Rules</h2>
              <ul style={s.ul}>
                <li>2–8 players per room.</li>
                <li>A game cannot start until at least 2 players have joined.</li>
                <li>Once a game starts, no additional players may join until it is over.</li>
                <li>Up to 10 concurrent rooms are supported.</li>
                <li>Spectator mode is not supported in v1.</li>
              </ul>

            </div>
          </div>
        </div>
      )}
    </>
  );
}
