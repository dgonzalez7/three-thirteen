# Data Model: "Push" Label for Go Out Button

**Phase**: 1 — Design & Contracts  
**Date**: 2026-03-14

---

## Overview

This feature requires **no new data model entities and no changes to existing models**. The condition driving the label change is already present in the existing `GameState` model.

---

## Relevant Existing Entities

### `GameState` (backend — `backend/game/state.py`)

The only field consumed by this feature:

| Field | Type | Description | Used by feature |
|-------|------|-------------|-----------------|
| `gone_out_player_id` | `Optional[str]` | Set to the `player_id` of the first player to go out this round; `None` before anyone goes out; reset to `None` at the start of each new round. | ✅ Read-only. Non-null value → show "Push". |

All other `GameState` fields are unchanged and unaffected.

### `PlayerState` (backend — `backend/game/state.py`)

| Field | Type | Description | Used by feature |
|-------|------|-------------|-----------------|
| `has_gone_out` | `bool` | `True` once this player has gone out in the current round. | ✅ Read-only (context only — the render guard already excludes this case). |

---

## Client-Side State (`GameRoom.jsx`)

No new React state variables are introduced.

| Existing variable | Type | Relevant usage |
|-------------------|------|---------------|
| `game` | `object \| null` | Full server `game_state` payload. `game.gone_out_player_id` drives the label. |
| `me` | `object \| null` | Derived from `game.players` for the local player. |

---

## State Transitions (unchanged)

The `gone_out_player_id` lifecycle is owned entirely by the server:

```
null  ──first go-out──→  "<player_id>"  ──advance_to_next_round──→  null
```

The frontend only reads this value — it never writes it.

---

## Summary

| Category | Change |
|----------|--------|
| New Pydantic models | None |
| Modified Pydantic models | None |
| New React state | None |
| Modified React state | None |
| New WebSocket messages | None |
| Modified WebSocket messages | None |
| New constants | None |
