# Research: "Push" Label for Go Out Button

**Phase**: 0 — Outline & Research  
**Date**: 2026-03-14  
**Feature**: Relabel the "Go Out" button as "Push" when at least one other player has already gone out in the current round.

---

## Summary of Findings

No NEEDS CLARIFICATION items exist in the Technical Context. All decisions are grounded in existing code.

---

## Decision 1: Where the condition lives

**Decision**: Read `game.gone_out_player_id` from the server-provided `game_state` payload already stored in React state.

**Rationale**: `gone_out_player_id` is already set by the server in `GameState` (non-null once the first player goes out) and is broadcast to all clients via the personalised `game_state` message. The condition requires zero new server fields, zero new message types, and zero new client state variables.

**Alternatives considered**:
- Introduce a separate `someone_went_out: bool` field — rejected; `gone_out_player_id !== null` already encodes this precisely.
- Track the condition locally in a `useState` variable on `player_went_out` message — rejected; would duplicate server truth and create a re-sync gap on reconnect (the `game_state` replay would not reset it correctly without extra logic).

---

## Decision 2: Scope of label change

**Decision**: Change only the button's text content (`'Go Out'` → conditional string). No changes to styling, handler, `disabled` state, or `title` attribute.

**Rationale**: The spec explicitly states: _"Behavior, placement, and styling are unchanged — only the label differs."_ The existing `s.btn('warning', false)` style and `handleEnterGoOutMode` handler are correct as-is.

**Alternatives considered**:
- Change button colour/style for "Push" — rejected by spec.
- Change `title` tooltip to mention "Push" — not required by spec; keep as-is to avoid scope creep.

---

## Decision 3: Exact condition

**Decision**: The label is `"Push"` when `game.gone_out_player_id !== null`. The button is only rendered inside the `canDiscard && !goOutMode` branch, which already ensures it is only visible on the player's own discard turn before they have gone out.

**Rationale**:
- `game.gone_out_player_id !== null` — someone has gone out this round (server truth).
- The button's render guard (`canDiscard && !goOutMode`) already excludes cases where `me.has_gone_out` is true (the player would have no further discard turns).

**Alternatives considered**:
- `game.phase === 'final_turns'` as the condition — rejected; using `phase` is less precise and couples the label to game phase rather than the semantic intent. A player's final turn begins when `gone_out_player_id` is set, which is the correct signal.

---

## Decision 4: Implementation location

**Decision**: Single inline change at line 785 of `frontend/src/components/GameRoom.jsx`.

Current code (line 785):
```jsx
  Go Out
```

Proposed code:
```jsx
  {game.gone_out_player_id ? 'Push' : 'Go Out'}
```

**Rationale**: The `game` object is already in scope at this render location (component-level state, non-null because the active-game view only renders when `game` is not null). No new variables, no new hooks, no new imports.

**Alternatives considered**:
- Derive a `goOutButtonLabel` constant in the derived-state block — acceptable but unnecessary for a one-liner; keeping it inline is idiomatic React for this codebase's style.

---

## Decision 5: Testing approach

**Decision**: Manual verification only. No automated frontend tests currently exist in the project.

**Rationale**: The project has no frontend test framework (no Jest, no Vitest, no Playwright). Adding one is out of scope for this change. The behaviour is trivially verifiable by starting a 2-player game and having one player go out — the other player's button should change label.

**Alternatives considered**:
- Add a Vitest/Jest test — out of scope; would require installing a test framework, configuring Vite for test mode, and mocking WebSocket state. Constitution §V prohibits introducing complexity without explicit architecture decision.

---

## No NEEDS CLARIFICATION Items

All unknowns are resolved. Research is complete.
