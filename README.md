# Three-Thirteen

A real-time multiplayer card game implementation using FastAPI WebSockets and React.

## Overview
Three-Thirteen is a server-authoritative multiplayer card game for 4-8 players. The game features real-time gameplay with WebSocket communication, room-based game instances, and comprehensive game logic on the server side.

## Technology Stack
- **Backend**: FastAPI, Pydantic, WebSockets, Python 3.11+
- **Frontend**: React 18, TypeScript, Vite, Tailwind CSS
- **DevOps**: Docker, Docker Compose, pytest

## Project Structure
```
three-thirteen/
├── docs/                    # Documentation
├── backend/                 # FastAPI server and game engine
│   ├── game/               # Core game logic
│   └── tests/              # Backend tests
├── frontend/               # React client
│   └── src/
│       ├── components/     # React components
│       └── hooks/          # Custom hooks
└── docker-compose.yml      # Development environment
```

## Quick Start
```bash
# Using Docker Compose (recommended)
docker-compose up --build

# Or run services separately
cd backend && uvicorn main:app --reload
cd frontend && npm run dev
```

## Game Features
- Real-time multiplayer gameplay
- Room-based game instances (max 10 rooms, 4-8 players each)
- Server-authoritative game logic
- WebSocket-based communication
- Immutable state management

## Documentation
- [Game Rules](docs/RULES.md)
- [Architecture](docs/ARCHITECTURE.md)
- [Development Setup](docs/DEVELOPMENT_SETUP.md)