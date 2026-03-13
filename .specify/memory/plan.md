# Implementation Plan: Copyright Footer

**Branch**: `main` | **Date**: 2026-03-12 | **Spec**: `.specify/memory/spec.md` §8 UI Layout — Copyright footer  
**Input**: Feature specification from `.specify/memory/spec.md`

---

## Summary

Add a discreet "Copyright 2026 Alea Iacta Est Game Foundry" notice to the bottom of every screen. The notice must use small text and low contrast so it does not compete with game elements. This is a **frontend-only change** — no backend code, no data model, no WebSocket messages, and no new dependencies are required.

Three React components are affected: `Lobby.jsx`, `PlayerLobby.jsx`, and `GameRoom.jsx`.

---

## Technical Context

**Language/Version**: JavaScript (JSX), React 18  
**Primary Dependencies**: Tailwind CSS (already configured)  
**Storage**: N/A  
**Testing**: Visual verification only — no logic to unit-test  
**Target Platform**: Browser (desktop, same as rest of v1)  
**Project Type**: Web application (frontend)  
**Performance Goals**: No impact — static text node  
**Constraints**: Must not interfere with any existing layout or game element  
**Scale/Scope**: 3 component files, 1–3 lines of JSX each

---

## Constitution Check

*GATE: Must pass before implementation.*

| Principle | Status | Notes |
|-----------|--------|-------|
| I. Server-Authoritative Architecture | ✅ PASS | No game logic on client. Static text only. |
| II. Real-Time Event-Driven Communication | ✅ PASS | No WebSocket changes. |
| III. Atomic & Immutable State Management | ✅ PASS | No state changes. |
| IV. Testable Game Engine | ✅ PASS | No engine changes. |
| V. Simplicity & In-Memory First | ✅ PASS | No new dependencies or infrastructure. |

No violations. Complexity tracking table not required.

---

## Project Structure

### Source Code

```text
frontend/
└── src/
    └── components/
        ├── Lobby.jsx          ← add footer
        ├── PlayerLobby.jsx    ← add footer
        └── GameRoom.jsx       ← add footer
```

No new files. No backend changes. No new dependencies.

---

## Phase 0: Research

### Decision Log

| Topic | Decision | Rationale |
|-------|----------|-----------|
| Shared component vs inline | Inline JSX in each component | Three screens, one line each — a shared component adds indirection with no benefit at this scale |
| Styling approach | Tailwind CSS utility classes | Tailwind is the project's configured styling framework; keeps styling co-located and consistent |
| Positioning | `fixed` bottom vs in-flow `footer` | In-flow `<footer>` inside each screen's root element — avoids z-index conflicts with modals (RulesModal uses `fixed`) |
| Contrast/size | `text-xs text-gray-400` (or equivalent low-contrast Tailwind classes) | Satisfies "small text, low contrast, unobtrusive" requirement from spec |

### Alternatives Considered

- **Shared `<CopyrightFooter />` component**: eliminated — three one-line usages don't justify a new file or import chain.
- **`position: fixed; bottom: 0`**: eliminated — the existing `RulesModal` is fixed-position and could overlap; in-flow footer avoids layering conflicts entirely.
- **CSS file addition**: eliminated — Tailwind inline classes are sufficient and consistent with the codebase's styling approach.

---

## Phase 1: Design & Contracts

### Data Model

None. This feature introduces no new data, state, or entities.

### Interface Contracts

None. This feature makes no changes to the WebSocket API, HTTP endpoints, or any server-side interface.

### Implementation Design

Each of the three screens renders a root container element. A `<footer>` element is appended as the last child of that root container, containing the copyright text. Tailwind classes enforce the visual treatment:

```jsx
<footer className="text-xs text-gray-400 text-center py-2">
  Copyright 2026 Alea Iacta Est Game Foundry
</footer>
```

**Exact classes** (subject to minor adjustment during implementation if the surrounding layout uses a different color scale):
- `text-xs` — smallest standard text size
- `text-gray-400` — low contrast against typical dark or light backgrounds
- `text-center` — centered across all screen widths
- `py-2` — minimal vertical breathing room

### Files to Modify

| File | Change |
|------|--------|
| `frontend/src/components/Lobby.jsx` | Append `<footer>` inside root container's JSX return |
| `frontend/src/components/PlayerLobby.jsx` | Append `<footer>` inside root container's JSX return |
| `frontend/src/components/GameRoom.jsx` | Append `<footer>` inside root container's JSX return |

### Verification

After implementation, manually verify:
1. Footer appears on the Lobby screen (room list).
2. Footer appears on the PlayerLobby screen (pre-game waiting room).
3. Footer appears on the GameRoom screen during active play, round-over panel, and game-finished leaderboard.
4. Footer does not overlap or obscure any game element, action button, or the RulesModal FAB.
5. Text is visibly smaller and lower contrast than surrounding UI text.

---

## Out of Scope

- Backend changes of any kind
- New React components or files
- Changes to `RulesModal.jsx`, `Scoreboard.jsx`, `CardView`, or `PlayerSeat`
- Mobile layout adjustments (post-v1 backlog per spec §13)
- Any animation, hover effects, or interactive behaviour on the footer
