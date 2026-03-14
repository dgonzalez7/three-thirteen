# Quickstart: "Push" Label for Go Out Button

**Phase**: 1 — Design & Contracts  
**Date**: 2026-03-14

---

## What This Feature Does

When a player is deciding whether to go out, the "Go Out" button is relabeled **"Push"** if at least one other player has already gone out this round. Behaviour, placement, and styling are unchanged — only the label differs.

---

## The Change in One Line

**File**: `frontend/src/components/GameRoom.jsx`  
**Line**: ~785 (inside the action buttons block, `canDiscard && !goOutMode` branch)

```jsx
// Before
  Go Out

// After
  {game.gone_out_player_id ? 'Push' : 'Go Out'}
```

---

## Local Development Setup

```bash
# Build and run the full stack
docker build -t three-thirteen .
docker run -p 8000:8000 three-thirteen
```

Open http://localhost:8000 in two browser tabs (or windows) to simulate two players.

---

## Verifying the Change

1. Open two browser tabs at http://localhost:8000.
2. Both tabs: select the same room and enter different player names.
3. Start the game.
4. **Player 1** (whichever tab has the current turn): draw a card, then look at the action buttons — button reads **"Go Out"**.
5. **Player 1**: click "Go Out", then click a card to go out with. Confirm the remaining hand is valid (e.g. a complete set). The server accepts.
6. **Player 2** now has their final turn. On their action buttons, the button should now read **"Push"** (not "Go Out").
7. Advance to round 2. At the start of the new round, the button should again read **"Go Out"** (because `gone_out_player_id` resets to `null`).

---

## Files Changed

| File | Change |
|------|--------|
| `frontend/src/components/GameRoom.jsx` | One-line label conditional on the Go Out button (~line 785) |

No backend files, no test files, no new dependencies.

---

## Constitution Compliance

| Principle | Compliance |
|-----------|-----------|
| Server-authoritative | ✅ Label derived from `game.gone_out_player_id` (server state) |
| Real-time communication | ✅ No WebSocket changes |
| Atomic state management | ✅ No state model changes |
| Testable game engine | ✅ No engine changes |
| Simplicity & in-memory first | ✅ Zero new dependencies; minimal diff |
