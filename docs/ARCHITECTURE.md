# Three-Thirteen Architecture

## System Overview
Server-authoritative real-time multiplayer card game using FastAPI WebSockets and React.

## Architecture Principles

### Server-Authoritative Design
- All game state and logic resides on server
- Client is purely a view layer
- No game logic implemented on frontend

### Real-Time Communication
- WebSocket-based bidirectional communication
- Event-driven architecture
- Room-based isolation for game instances

### State Management
- Immutable state objects
- Atomic state updates
- Complete state synchronization to all room participants

## Backend Architecture

### FastAPI Application
- REST API for lobby/room management
- WebSocket endpoints for real-time gameplay
- Dependency injection for services

### Game Engine
- Pure functions for game logic
- Rule validation engine
- Event system for game events

### Room Management
- Lifecycle management (create, join, leave, cleanup)
- Player limits enforcement
- Connection handling

## Frontend Architecture

### React Application
- Component-based UI
- Custom WebSocket hook
- State lifting and controlled components

### WebSocket Integration
- Centralized connection management
- Event mapping to state updates
- Error boundaries and reconnection

## Technology Stack
- **Backend**: FastAPI, Pydantic, WebSockets, Python 3.11+
- **Frontend**: React 18, TypeScript, Vite, Tailwind CSS
- **DevOps**: Docker, Docker Compose, pytest
