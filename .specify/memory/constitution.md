<!--
SYNC IMPACT REPORT
==================
Version change: (none — initial fill from template) → 1.0.0
Modified principles: N/A (initial population)
Added sections: Core Principles, Technology Stack, Deployment Policy,
  Development Guidelines, Governance
Removed sections: N/A
Templates requiring updates:
  ✅ constitution.md — filled from .windsurfrules (this file)
  ✅ plan-template.md — Constitution Check gates align with principles below
  ✅ spec-template.md — no mandatory sections conflict with these principles
  ✅ tasks-template.md — task categories align with principles below
Corrections applied vs original .windsurfrules:
  - Removed: AWS ECR build/push and GitHub Actions deployment references
  - Removed: free-tier spin-down language
  - Added: infrastructure/ locked as legacy (MUST NOT be modified)
Deferred TODOs: none
-->

# Three-Thirteen Constitution

## Core Principles

### I. Server-Authoritative Architecture (NON-NEGOTIABLE)

All game state, logic, and validation MUST reside on the server. The frontend
MUST only render state received from the server and send user action events —
it MUST NOT implement game rules, scoring, or state transitions. The server
MUST validate every incoming action, including those from ostensibly trusted
clients.

**Rationale**: A multiplayer card game’s integrity depends on a single trusted
arbiter. Client-side logic creates cheating vectors and state divergence that
cannot be corrected without a full reconnect.

### II. Real-Time Event-Driven Communication

WebSocket connections (FastAPI) MUST be used for all in-game communication.
The server MUST emit events; clients subscribe and react. Each game instance
MUST be isolated in its own room. All players in a room MUST see identical
game state simultaneously — partial or staggered broadcasts are not permitted.

**Rationale**: Card game turns are low-latency, ordered events. Polling or
REST calls for turn progression create unacceptable race conditions and UX
degradation.

### III. Atomic & Immutable State Management

Game state objects MUST be treated as immutable — mutations produce new state
objects rather than modifying in-place. All state transitions MUST be atomic
and transactional. Complete state changes MUST be broadcast to all room
participants; partial diffs that could leave clients inconsistent are not
permitted.

**Rationale**: In-memory state (v1 constraint, no database) must be
self-consistent at every observable boundary. Immutability makes bugs
reproducible and state easier to reason about.

### IV. Testable Game Engine

All game logic MUST be implemented as pure functions:
`(state, action) → new_state`. Game engine functions MUST be unit-testable
without WebSocket or HTTP dependencies. Rule validation MUST be separated
from state management. `docs/RULES.md` is the canonical source of truth for
game rules — any ambiguity MUST be resolved there, not in code comments.

**Rationale**: The game engine is the most complex and failure-prone layer.
Pure functions with no I/O dependencies enable fast, deterministic tests and
confident refactoring.

### V. Simplicity & In-Memory First

v1 uses in-memory state only — no database, no external caches. Persistence
layers, queues, or external services MUST NOT be introduced without an
explicit architecture decision. Room model constraints (max 10 rooms,
2–8 players per room) MUST be enforced. New complexity MUST be justified
against the existing working system.

**Rationale**: This is a brownfield project with a functioning codebase.
Premature infrastructure adds operational risk without user benefit.

## Technology Stack

### Backend
- **Runtime**: Python 3.11+
- **Framework**: FastAPI (WebSocket server + HTTP API)
- **Validation**: Pydantic (all API models MUST use Pydantic)
- **Async**: All I/O operations MUST be async/await
- **Testing**: pytest — all game logic MUST have unit tests

### Frontend
- **Framework**: React 18
- **Language**: JavaScript (MUST be used for all frontend code)
- **Build tool**: Vite
- **Styling**: Tailwind CSS
- **Patterns**: Controlled components; WebSocket logic centralized in a custom
  hook; `React.memo` / `useCallback` / `useMemo` for performance-critical paths

### DevOps
- **Containerization**: Docker (single multi-stage image: Node builds frontend,
  Python serves backend + static files)
- **Local development**: `docker build -t three-thirteen . && docker run -p 8000:8000 three-thirteen` → http://localhost:8000
- **Linting/formatting**: ESLint + Prettier (JS), Black (Python)

## Deployment Policy

Production deployment is **Render.com only**.

- **Production URL**: https://three-thirteen.onrender.com
- **Deploy trigger**: automatic on every push to `main` via Render’s GitHub
  integration
- **Artifact**: Docker image built from the root `Dockerfile` (multi-stage)
- **Health check**: `GET /api/health`
- **WebSockets**: fully supported (`wss://` in production)

The `infrastructure/` directory contains legacy Terraform files and MUST NOT
be modified or used. It is retained for historical reference only.

No AWS, ECR, or App Runner deployment pipelines are active or maintained. Any
GitHub Actions workflows that reference AWS infrastructure are superseded by
Render’s direct GitHub integration and MUST NOT be re-enabled.

## Development Guidelines

### Code Quality
- Python: type hints MUST be used on all functions and methods
- Frontend: JavaScript (JSX); no unsafe patterns or implicit globals
- Formatting enforced: Prettier (JS), Black (Python)

### Security
- All user inputs MUST be validated server-side
- Player identification and room access MUST be secured
- All data MUST be sanitized before storage or broadcast

### Testing Discipline
- All game logic and business rules MUST have unit tests
- WebSocket communication and room management MUST have integration tests
- E2E tests for critical user journeys are a future requirement (not a current gate)

## Governance

This constitution supersedes all other project conventions. Any practice that
conflicts with a principle above MUST be changed, not the principle.

**Amendment procedure**:
1. Identify the principle requiring change and document the rationale.
2. Bump the version per semantic versioning:
   - MAJOR — principle removal or backward-incompatible redefinition
   - MINOR — new principle or material expansion
   - PATCH — clarification or wording refinement
3. Update `LAST_AMENDED_DATE` to the amendment date (ISO format YYYY-MM-DD).
4. Propagate changes to all dependent templates in `.specify/templates/`.
5. Prepend a new Sync Impact Report comment to this file.

All feature plans and tasks MUST include a Constitution Check gate verifying
compliance with the five core principles before implementation begins.

Runtime development guidance lives in `.windsurfrules` — that file MUST
remain consistent with this constitution.

**Version**: 1.0.0 | **Ratified**: 2026-03-12 | **Last Amended**: 2026-03-12
