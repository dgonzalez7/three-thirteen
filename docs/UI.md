# Three Thirteen — Game Room UI Specification

## Design Philosophy
The v1 game room UI prioritizes **correct gameplay** over visual polish. The layout should be functional and clear. A graphically enhanced UI is planned for a future version once game logic is proven correct.

---

## Game Room Screen

### Screen Contents
The game room screen displays the following at all times:

- **Round indicator** — current round number and the associated wild card rank (e.g. "Round 3 — Wild: 5s")
- **Draw pile** — face-down stack; shows a card back
- **Discard pile** — face-up stack; shows only the top card
- **Player's own hand** — all cards visible to the player, in their current arrangement
- **Other players** — each player's name and current score, arranged to suggest a table layout
- **Turn indicator** — diamond symbols (♦) surrounding the active player's name highlight whose turn it is
- **Current scores** — displayed for all players throughout the game

---

### Screen Layout

The screen is shown from each player's own **vantage point** — they always see themselves at the bottom of the table. Other players are arranged above, suggesting a clockwise seating order.

```
┌─────────────────────────────────────┐
│  Round 3 — Wild Card: 5s            │
│                                     │
│  Other Players:                     │
│                                     │
│  Matt          ♦ Judi ♦             │
│  Score: 17     Score: 42            │
│                                     │
│  [ Draw Pile 🂠 ]  [ Discard: K♥ ]  │
│                                     │
│  Dave — Score: 22                   │
│  Hand:                              │
│  [3♠][3♥][5♣][7♦][9♠][K♣]          │
│                                     │
│  [ Draw from Pile ]                 │
│  [ Draw from Discard ]              │
│  [ Discard a Card ]                 │
└─────────────────────────────────────┘
```

- The **current player** (Dave in this example) is always shown at the bottom
- Other players are arranged across the top, left to right in clockwise order
- ♦ diamonds ♦ around a name indicate it is that player's turn
- Other players' cards are **not shown** — only their card count is visible

---

## Game Controls

### Rearranging Cards
A player may rearrange the cards in their hand **at any time**, including when it is not their turn. This helps them plan their sets and runs.

---

### On Your Turn
A player's turn proceeds in this sequence:

**Step 1 — Draw (required)**
The player must choose one of:
- Draw the top face-down card from the draw pile
- Draw the top face-up card from the discard pile

**Step 2 — Attempt to Go Out or Discard**
After drawing, the player must either:
- **Discard** — select a card from their hand and discard it. Play passes to the next player.
- **Attempt to Go Out** — click the "Go Out" button, then select the card to discard. The server validates that the remaining hand forms valid sets and runs with zero unmatched cards. If valid, the player goes out and scores 0. If invalid, the server rejects the action and the player must discard normally instead.

---

### When It Is Not Your Turn
- The player can observe all game activity
- The player can see the top card of the discard pile
- The player can see the turn indicator highlighting the active player
- The player can rearrange their own hand freely

---

## Game Events & Messages

### Player Goes Out
When a player goes out, a message is displayed to **all players**:

> "🃏 [Player Name] has gone out! Each remaining player gets one final turn."

This message persists while the remaining players take their final turns.

---

### End of Round
After all final turns are taken, each player's unmatched cards and penalty points are revealed. A round summary is displayed showing:
- Each player's combinations laid out
- Each player's penalty cards
- Points scored this round
- Cumulative scores to date

---

### End of Game
After round 11, the final scores are displayed in order from lowest (winner) to highest:

```
🏆 Game Over!

1st  Dave    42 pts  ← Winner!
2nd  Judi    67 pts
3rd  Matt    89 pts
```

---

## Table Perspective
Each player's screen shows the game from **their own seat**. The current player is always at the bottom. Other players are positioned around the top of the screen in clockwise order, so the player to the left appears on the left side and the player to the right appears on the right side.

---

## Future Enhancements (Post-v1)
- Graphically rendered playing cards
- Animated card draws and discards
- Visual card grouping for sets and runs
- Table felt background and polished player avatars
- Sound effects
- Mobile-responsive layout
