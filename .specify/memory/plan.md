# Implementation Plan: "Push" Label for Go Out Button

**Branch**: `main` | **Date**: 2026-03-14 | **Spec**: `.specify/memory/spec.md`  
**Input**: Feature specification from `.specify/memory/spec.md`

**Note**: This is a brownfield plan covering the Three-Thirteen codebase as it exists today, plus the targeted change to relabel the "Go Out" button as "Push" when at least one other player has already gone out in the current round.

## Summary

The primary requirement is a **purely cosmetic frontend label change**: the "Go Out" action button in `GameRoom.jsx` must display "Push" instead of "Go Out" whenever `game.gone_out_player_id` is non-null and the viewing player has not yet gone out. No server changes are required — the condition is already fully expressed in the `game_state` payload (`gone_out_player_id`). The implementation is a one-line conditional in the button's label expression.

## Technical Context

**Language/Version**: Python 3.11+ (backend) / JavaScript ESNext with JSX (frontend)  
**Primary Dependencies**: FastAPI, Pydantic, WebSockets (backend); React 18, Vite (frontend)  
**Storage**: In-memory only — no database, no persistence layer  
**Testing**: pytest (backend unit + integration); no frontend test framework currently present  
**Target Platform**: Linux server (Render.com, Docker); browser (Chrome/Firefox/Safari)  
**Project Type**: Real-time multiplayer web application  
**Performance Goals**: No new performance requirements — this is a label change  
**Constraints**: No new dependencies allowed (Constitution §V — Simplicity & In-Memory First); frontend must remain plain JavaScript (no TypeScript migration)  
**Scale/Scope**: Up to 10 concurrent rooms, 2–8 players per room

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Principle | Status | Notes |
|-----------|--------|-------|
| **I. Server-Authoritative Architecture** | ✅ PASS | Label change is purely presentational. The condition (`gone_out_player_id != null`) is derived from server-provided `game_state`. No client-side game logic added. |
| **II. Real-Time Event-Driven Communication** | ✅ PASS | No changes to WebSocket protocol or broadcast mechanics. |
| **III. Atomic & Immutable State Management** | ✅ PASS | No state model changes. `gone_out_player_id` already exists in `GameState`. |
| **IV. Testable Game Engine** | ✅ PASS | No engine changes. The condition is a read-only check on existing state. |
| **V. Simplicity & In-Memory First** | ✅ PASS | Zero new dependencies, no infrastructure changes. Minimal diff. |

**Constitution Check result: ALL GATES PASS. Proceed to Phase 0.**

## Project Structure

### Documentation (this feature)

```text
.specify/memory/
├── plan.md              # This file
├── research.md          # Phase 0 output
├── data-model.md        # Phase 1 output
├── quickstart.md        # Phase 1 output
├── contracts/           # Phase 1 output
└── tasks.md             # Phase 2 output (/speckit.tasks — NOT created by /speckit.plan)
```

### Source Code (repository root)

```text
backend/
├── game/
│   ├── engine.py          # Pure game logic (no changes required)
│   ├── state.py           # Pydantic models (no changes required)
│   ├── room_manager.py    # Orchestration layer (no changes required)
│   └── events.py          # Unused event bus (no changes required)
├── main.py                # FastAPI entrypoint (no changes required)
└── tests/
    ├── test_engine.py
    ├── test_rooms.py
    └── test_simulation.py

frontend/
└── src/
    ├── App.jsx
    ├── components/
    │   ├── GameRoom.jsx   # ← ONLY FILE CHANGED: button label conditional
    │   ├── Lobby.jsx
    │   ├── PlayerLobby.jsx
    │   ├── RulesModal.jsx
    │   └── Scoreboard.jsx
    └── hooks/
        └── useWebSocket.js
```

**Structure Decision**: Web application layout. The single changed file is `frontend/src/components/GameRoom.jsx`. All other files are listed for orientation but require no modification.

## Complexity Tracking

> No Constitution Check violations. Section not applicable.
