import React, { useState } from 'react';

const RULES_TEXT = `Three Thirteen — House Rules

OVERVIEW
Three Thirteen is a multiplayer card game for 2–8 players. It is part of the Rummy family. The goal is to form sets and runs with the cards in your hand, accumulating the fewest possible penalty points over 11 rounds of gameplay.

Note: These are house rules and represent a variant of the published rules.

─────────────────────────────────────────
PLAYERS
2 to 8 players.

─────────────────────────────────────────
DECK
The number of standard 52-card decks used depends on the number of players:

  Players 2–3 → 1 deck
  Players 4–5 → 2 decks
  Players 6–8 → 3 decks

Aces are LOW in runs (A-2-3 is valid; Q-K-A is not), but count HIGH (15 points) as penalty cards.

─────────────────────────────────────────
SETUP
The first dealer is chosen randomly. After each round, the deal passes to the left.

Cards dealt per round:

  Round 1  → 3 cards   Wild: 3s
  Round 2  → 4 cards   Wild: 4s
  Round 3  → 5 cards   Wild: 5s
  Round 4  → 6 cards   Wild: 6s
  Round 5  → 7 cards   Wild: 7s
  Round 6  → 8 cards   Wild: 8s
  Round 7  → 9 cards   Wild: 9s
  Round 8  → 10 cards  Wild: 10s
  Round 9  → 11 cards  Wild: Jacks
  Round 10 → 12 cards  Wild: Queens
  Round 11 → 13 cards  Wild: Kings

All remaining cards form the draw pile face-down. The top card is turned face-up to start the discard pile.

─────────────────────────────────────────
WILD CARDS
In each round, one rank of card is wild (see table above). Wild cards may be substituted for any card in a set or run. Wild cards count as their face value if left in hand as penalty cards.

─────────────────────────────────────────
GAMEPLAY
The player to the left of the dealer goes first. Play continues clockwise.

On each turn, a player must:
  1. Draw — take either the top face-down card from the draw pile, or the top face-up card from the discard pile.
  2. Discard — place one card face-up on the discard pile (unless going out).

─────────────────────────────────────────
SETS AND RUNS
Players aim to arrange their cards into valid combinations:

  Set — three or more cards of the same rank (e.g. 7♠ 7♥ 7♦).
  Run — three or more cards of the same suit in sequence (e.g. A♥ 2♥ 3♥).

Additional rules:
  • Sets and runs may contain more than three cards.
  • No card may belong to more than one combination.
  • Any combination of sets and runs is valid.
  • Players may NOT add cards to another player's combinations.

─────────────────────────────────────────
GOING OUT
A player may go out on their turn if, after drawing, they can arrange all of their cards into sets and runs with exactly one card left over to discard.

To go out, a player:
  1. Announces they are going out.
  2. Lays their sets and runs face-up on the table.
  3. Discards their final card.

After a player goes out, each remaining player gets one final turn (clockwise), then the round ends and scoring takes place.

Only one player may go out per round. If a subsequent player, during their final turn, can also go out, they score 0 points but the original going-out player remains recorded.

─────────────────────────────────────────
SCORING
After the final turn, all players arrange their hands into as many valid sets and runs as possible. Unmatched cards score penalty points:

  Ace         → 15 points
  King        → 10 points
  Queen       → 10 points
  Jack        → 10 points
  2 through 10 → Face value
  Wild card   → Face value

The player who went out scores 0 points for that round.

─────────────────────────────────────────
NEW ROUND
After rounds 1–10, all cards are reshuffled and a new round begins with the deal passing to the left.

─────────────────────────────────────────
WINNING
After the 11th round, the player with the lowest cumulative score wins.

─────────────────────────────────────────
ROOM RULES
  • 2–8 players per room.
  • A game cannot start until at least 2 players have joined.
  • Once a game starts, no additional players may join until it is over.
  • Up to 10 concurrent rooms are supported.
  • Spectator mode is not supported in v1.
`;

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
  pre: {
    margin: 0,
    whiteSpace: 'pre-wrap',
    wordBreak: 'break-word',
    fontFamily: "'Segoe UI', system-ui, sans-serif",
    fontSize: '0.85rem',
    lineHeight: 1.7,
    color: '#cbd5e1',
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
              <pre style={s.pre}>{RULES_TEXT}</pre>
            </div>
          </div>
        </div>
      )}
    </>
  );
}
