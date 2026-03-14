# UI Contracts: "Push" Label for Go Out Button

**Phase**: 1 — Design & Contracts  
**Date**: 2026-03-14

---

## Overview

This document defines the UI contract for the Go Out / Push button in `GameRoom.jsx`. A UI contract specifies what the component presents to the user under each observable condition, independently of implementation details.

---

## Button: Go Out / Push

### Location

`GameRoom.jsx` → active-game view → action row below the player's hand.

### Visibility Contract

The button is **only visible** when all of the following are true:

| Condition | Value |
|-----------|-------|
| It is the local player's turn | `isMyTurn === true` |
| The turn phase is discard | `game.turn_phase === 'discard'` |
| The game phase permits discarding | `game.phase === 'playing' OR 'final_turns'` |
| The player is not already in go-out mode | `goOutMode === false` |

When the button is not visible, the player sees either the draw controls (draw phase) or the go-out card-selection prompt (go-out mode).

### Label Contract

| Condition | Label displayed |
|-----------|----------------|
| No player has gone out this round (`game.gone_out_player_id === null`) | **"Go Out"** |
| At least one player has already gone out this round (`game.gone_out_player_id !== null`) | **"Push"** |

### Behaviour Contract (unchanged by this feature)

| Property | Value |
|----------|-------|
| Action on click | Enters go-out mode (`goOutMode = true`); clears selected card and error |
| Style | Warning/amber colour (`s.btn('warning', false)`) |
| Disabled state | Never disabled (button is hidden entirely when it is not the player's turn) |
| Tooltip (`title`) | `"Server validates your remaining hand forms valid sets/runs"` |

### Invariants

1. The label change is **cosmetic only** — clicking "Push" invokes the same handler and same server message (`go_out`) as clicking "Go Out".
2. The button must never appear when `me.has_gone_out === true` (the player already went out this round and has no further discard turns).
3. Label reverts to "Go Out" at the start of a new round (when `game.gone_out_player_id` resets to `null`).

---

## WebSocket Contract (unchanged)

The `go_out` message sent by this button is not affected:

```json
{ "type": "go_out", "room_id": "room-1", "card_id": "<selected_card_id>" }
```

No new message types. No changes to payload shape.

---

## Server Contract (unchanged)

`attempt_go_out` in `engine.py` validates the hand and rejects with an `error` message if the remaining hand has non-zero penalty points. This validation is unchanged — "Push" is purely a UI affordance; the server does not distinguish between a "Go Out" attempt and a "Push" attempt.
