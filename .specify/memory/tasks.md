# Tasks: "Push" Label for Go Out Button

**Input**: `.specify/memory/plan.md`, `.specify/memory/spec.md`, `.specify/memory/research.md`, `.specify/memory/data-model.md`, `.specify/memory/contracts/ui-contracts.md`  
**Prerequisites**: plan.md ✅ spec.md ✅ research.md ✅ data-model.md ✅ contracts/ ✅

**Tests**: Not requested — no frontend test framework exists; manual verification only (see quickstart.md).

**Organization**: Single user story. One implementation task (one file, one line). Verification tasks are independent and parallelizable.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[US1]**: "Push" label for Go Out button

---

## Phase 1: Setup

**Purpose**: Confirm the existing codebase state before making the change.

- [ ] T001 Read `frontend/src/components/GameRoom.jsx` lines 780–795 to confirm the "Go Out" button text is still a plain string literal `Go Out` (not yet conditional) and that `game.gone_out_player_id` is accessible in scope at that render location

---

## Phase 2: User Story 1 — Conditional "Push" / "Go Out" Label (Priority: P1) 🎯 MVP

**Goal**: The Go Out button displays "Push" when `game.gone_out_player_id` is non-null (someone has already gone out this round), and "Go Out" otherwise. Behaviour, placement, and styling are unchanged.

**Independent Test**: Start a 2-player game. Before anyone goes out, confirm the button reads "Go Out". Have Player 1 successfully go out. On Player 2's final turn, confirm the button now reads "Push". Advance to the next round and confirm the button reverts to "Go Out". (See `.specify/memory/quickstart.md` for full steps.)

### Implementation

- [ ] T002 [US1] In `frontend/src/components/GameRoom.jsx` (~line 785), replace the static label `Go Out` with `{game.gone_out_player_id ? 'Push' : 'Go Out'}` inside the Go Out button's JSX

**Exact change:**
```jsx
// Before (line ~785)
  Go Out

// After
  {game.gone_out_player_id ? 'Push' : 'Go Out'}
```

**Checkpoint**: The single line is changed. No other lines in the file are modified. Confirm no lint errors.

---

## Phase 3: Verification

**Purpose**: Manually confirm all label contract conditions from `.specify/memory/contracts/ui-contracts.md`.

- [ ] T003 [P] Verify label reads "Go Out" during `playing` phase before anyone has gone out — start a game and inspect the button on the active player's discard turn
- [ ] T004 [P] Verify label reads "Push" during `final_turns` phase after the first player has gone out — have a player go out and inspect the next player's button
- [ ] T005 [P] Verify label reverts to "Go Out" at the start of round 2 — advance to the next round and confirm `gone_out_player_id` resets
- [ ] T006 Verify button behaviour is unchanged — clicking "Push" enters go-out mode identically to clicking "Go Out"; server accepts or rejects normally

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies — start immediately
- **Implementation (Phase 2)**: Depends on T001 confirming the code location
- **Verification (Phase 3)**: Depends on T002 complete; T003/T004/T005 can run in parallel; T006 after T003–T005

### User Story Dependencies

- **US1**: No dependencies on any other story or file. Self-contained one-line frontend change.

### Parallel Opportunities

```
T001 (read file to confirm)
  ↓
T002 (make the change)
  ↓
T003 — verify "Go Out" label (no-one out yet)
T004 — verify "Push" label (after first go-out)   ← T003/T004/T005 in parallel
T005 — verify revert on new round
  ↓
T006 — verify behaviour unchanged
```

---

## Implementation Strategy

### MVP (complete feature in one pass)

1. Complete T001 — confirm code location
2. Complete T002 — make the one-line change
3. Complete T003, T004, T005 in parallel — verify all label conditions
4. Complete T006 — verify behaviour unchanged

Total: **6 tasks**, 1 file changed, 1 line modified, no backend work, no new dependencies.

---

## Notes

- [P] tasks = no file conflicts, no shared state dependencies
- Only `frontend/src/components/GameRoom.jsx` is modified
- No backend changes of any kind
- No new React state, no new hooks, no new imports
- `infrastructure/` MUST NOT be touched (constitution §Deployment Policy)
- `game.gone_out_player_id` is already in scope — it is part of the `game` state object set by the `game_state` WebSocket message
