# Tasks: Copyright Footer

**Input**: `.specify/memory/plan.md`, `.specify/memory/spec.md`  
**Prerequisites**: plan.md ✅ spec.md ✅

**Tests**: Not requested — static UI text, no logic to unit-test.

**Organization**: Single user story. All three implementation tasks are independent (different files) and can be executed in parallel.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[US1]**: Copyright Footer user story

---

## Phase 1: Setup

**Purpose**: Confirm the visual treatment (Tailwind classes) before touching any component.

- [ ] T001 Verify Tailwind CSS is configured and `text-xs`, `text-gray-400`, `text-center`, `py-2` classes are available in `frontend/tailwind.config.js` (or equivalent config) — no file change required if already present

---

## Phase 2: User Story 1 — Copyright Footer on All Screens (Priority: P1) 🎯 MVP

**Goal**: Display "Copyright 2026 Alea Iacta Est Game Foundry" at the bottom of every screen using small, low-contrast text that does not compete with game elements.

**Independent Test**: Navigate to each of the three screens (Lobby, PlayerLobby, GameRoom) and confirm the copyright text appears at the bottom of each with visibly smaller and lower-contrast styling than surrounding UI. Confirm the RulesModal FAB and all action buttons remain unobscured.

### Implementation

- [ ] T002 [P] [US1] Add `<footer>` with copyright text as last child of root container in `frontend/src/components/Lobby.jsx`
- [ ] T003 [P] [US1] Add `<footer>` with copyright text as last child of root container in `frontend/src/components/PlayerLobby.jsx`
- [ ] T004 [P] [US1] Add `<footer>` with copyright text as last child of root container in `frontend/src/components/GameRoom.jsx`

**Footer JSX for all three files:**
```jsx
<footer className="text-xs text-gray-400 text-center py-2">
  Copyright 2026 Alea Iacta Est Game Foundry
</footer>
```

**Checkpoint**: All three screens show the copyright footer. Verify each independently before marking complete.

---

## Phase 3: Polish & Verification

**Purpose**: Cross-screen consistency check and spec sign-off.

- [ ] T005 [P] Visually verify footer on Lobby screen — confirm small text, low contrast, not overlapping RulesModal FAB
- [ ] T006 [P] Visually verify footer on PlayerLobby screen — confirm small text, low contrast, not overlapping any element
- [ ] T007 [P] Visually verify footer on GameRoom screen — confirm footer visible during active play, round-over panel, and game-finished leaderboard views without obscuring action buttons or RulesModal FAB
- [ ] T008 Update `.specify/memory/spec.md` if any implementation detail differs from the spec description (e.g. exact Tailwind classes used)

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies — can start immediately
- **Implementation (Phase 2)**: Depends on T001 confirming Tailwind classes available
- **Polish (Phase 3)**: Depends on T002, T003, T004 all complete

### User Story Dependencies

- **US1**: No dependencies on other user stories. Self-contained frontend change.

### Within Phase 2

- T002, T003, T004 are fully independent — different files, no shared state, can be done in any order or simultaneously.

### Parallel Opportunities

```
After T001:
  T002 — Lobby.jsx
  T003 — PlayerLobby.jsx     ← all three in parallel
  T004 — GameRoom.jsx

After T002 + T003 + T004:
  T005 — verify Lobby
  T006 — verify PlayerLobby   ← all three in parallel
  T007 — verify GameRoom
```

---

## Implementation Strategy

### MVP (complete feature in one pass)

1. Complete T001 — confirm Tailwind config
2. Complete T002, T003, T004 in parallel — add footer to all three components
3. Complete T005, T006, T007 — visual verification
4. Complete T008 — update spec if needed

Total: **8 tasks**, all in one story, no backend work.

---

## Notes

- [P] tasks = different files, no dependencies between them
- No new files required — edits only
- No backend changes of any kind
- No new dependencies
- `infrastructure/` MUST NOT be touched (constitution §Deployment Policy)
