# Three-Thirteen — Feature Specification

_Brownfield spec. Describes the system as it exists today. Sources: `docs/RULES.md`, `docs/UI.md`, `docs/codebase-research.md`._

---

## Table of Contents

1. [Overview](#1-overview)
2. [Game Rules](#2-game-rules)
3. [Room & Lobby Rules](#3-room--lobby-rules)
4. [System Architecture](#4-system-architecture)
5. [Backend Modules](#5-backend-modules)
6. [Data Models](#6-data-models)
7. [WebSocket API](#7-websocket-api)
8. [Frontend](#8-frontend)
9. [Game Phase State Machine](#9-game-phase-state-machine)
10. [Deployment](#10-deployment)
11. [Test Coverage](#11-test-coverage)
12. [Known Dead Code](#12-known-dead-code)
13. [Post-v1 Backlog](#13-post-v1-backlog)

---

## 1. Overview

Three-Thirteen is a real-time multiplayer card game (Rummy family) playable in a web browser. Players accumulate the fewest penalty points over 11 rounds; the player with the lowest cumulative score wins.

The application is a single deployable unit: a FastAPI backend serves both the WebSocket/HTTP API and the pre-built React frontend as static files.

**Technology stack:**

| Layer | Technology |
|-------|-----------|
| Backend | Python 3.11+, FastAPI, Pydantic, WebSockets |
| Frontend | React 18, Vite, Tailwind CSS |
| State store | In-memory only (no database) |
| Deployment | Docker (single container), Render.com |

---

## 2. Game Rules

### Players & Decks

- 2–8 players per game.
- Number of standard 52-card decks scales with player count:

| Players | Decks |
|---------|-------|
| 2–3 | 1 |
| 4–5 | 2 |
| 6–8 | 3 |

- Aces are **low** in runs (A-2-3 valid; Q-K-A invalid) and worth **15 penalty points**.

### Rounds

The game consists of exactly 11 rounds. Each round deals more cards and uses a different wild rank:

| Round | Cards Dealt | Wild Card |
|-------|-------------|-----------|
| 1 | 3 | 3s |
| 2 | 4 | 4s |
| 3 | 5 | 5s |
| 4 | 6 | 6s |
| 5 | 7 | 7s |
| 6 | 8 | 8s |
| 7 | 9 | 9s |
| 8 | 10 | 10s |
| 9 | 11 | Jacks |
| 10 | 12 | Queens |
| 11 | 13 | Kings |

- The first dealer is chosen randomly. After each round, the deal passes to the left.
- All remaining cards after dealing form the face-down **draw pile**. The top card is flipped face-up to start the **discard pile**.

### Wild Cards

- The wild rank for a round is determined by the table above.
- Wilds substitute for any card in a set or run.
- Wilds left unmatched at scoring count at their face value as penalty points.

### Turn Structure

Play proceeds clockwise, starting with the player to the left of the dealer.

Each turn:
1. **Draw** — take the top face-down card from the draw pile, or the top face-up card from the discard pile.
2. **Discard or Go Out** — either discard one card to the discard pile, or attempt to go out.

### Sets and Runs

- **Set** — three or more cards of the same rank (e.g. 7♠ 7♥ 7♦).
- **Run** — three or more cards of the same suit in ascending sequence (e.g. A♥ 2♥ 3♥).
- Combinations may contain more than three cards.
- A card may not belong to more than one combination.
- Players may not add cards to another player's laid-down combinations.

### Going Out

After drawing, a player may go out if they can arrange **all** cards into valid sets/runs with exactly **one card left over** to discard.

To go out:
1. Player clicks "Go Out" and selects the discard card.
2. Server validates that the remaining hand (after removing the chosen card) has zero penalty points.
3. If valid: the card is discarded, the player's round score is set to 0, phase transitions to `FINAL_TURNS`.
4. If invalid: the server rejects the action with an `error` message; the player must discard normally.

After the first player goes out, each remaining player gets **one final turn**. Only the first player to go out triggers the final-turn sequence. A subsequent player who also goes out during their final turn scores 0 for the round but does not restart the sequence.

### Scoring

After all final turns, players lay out their best sets and runs. Unmatched cards are penalty points:

| Card | Penalty |
|------|---------|
| Ace | 15 |
| King | 10 |
| Queen | 10 |
| Jack | 10 |
| 2–10 | Face value |
| Wild card | Face value |

The player who went out scores **0 points**. Cumulative scores accumulate across all 11 rounds.

### Winning

After round 11, the player with the **lowest cumulative score** wins.

---

## 3. Room & Lobby Rules

- The system supports up to **10 concurrent rooms** (`room-1` through `room-10`).
- Each room holds **2–8 players**.
- A game cannot start until at least **2 named players** are in the room's pre-game lobby.
- Once a game is `IN_GAME`, no new players may join that room.
- Spectator mode is not supported.
- If all WebSocket connections drop during an active game, the room is automatically reset after **5 minutes** (300 seconds) of inactivity.

---

## 4. System Architecture

### Design Principles

- **Server-authoritative**: all game logic, validation, and state transitions run on the server. The client is a pure view.
- **Event-driven real-time**: state changes are broadcast to all room participants via WebSocket immediately after each action.
- **Private views**: each player's `game_state` payload hides opponent hands and the draw pile contents; only counts are exposed.
- **In-memory state**: all state lives in `RoomManager`; there is no database persistence.

### Process Model

One global `RoomManager` instance is created at startup and shared across all requests. The 10 room slots are fixed at startup.

### Endpoints

| Type | Path | Description |
|------|------|-------------|
| HTTP GET | `/api/health` | Health check |
| HTTP GET | `/health` | Health check (alias) |
| HTTP GET | `/rooms` | JSON snapshot of all 10 rooms |
| WebSocket | `/ws/lobby` | Lobby watchers — receives `rooms_update` broadcasts |
| WebSocket | `/ws/room/{room_id}?player_id=…` | Room participants — full game communication |

Built React static files are served from `backend/static/` in production (the path is mounted only when the directory exists).

---

## 5. Backend Modules

### `backend/main.py`

FastAPI app entry point. Handles HTTP and WebSocket routing only. Delegates all game logic to `RoomManager`.

- On WebSocket connect to a room: sends an initial `lobby_update` snapshot.
- Routes incoming room messages by `type` field to the appropriate `RoomManager.handle_*` method.

### `backend/game/state.py`

Data definitions only — no logic.

- Enums: `Suit`, `Rank`, `GamePhase`, `TurnPhase`, `RoomStatus`
- Constants: `RANK_ORDER`, `RANK_POINTS`, `ROUND_WILD`, `decks_for_players`
- Pydantic models: `Card`, `PlayerState`, `RoundResult`, `GameState`, `LobbyPlayer`, `RoomState`

### `backend/game/engine.py`

Pure functional game logic — no I/O, no WebSocket dependencies, fully unit-testable.

| Function | Responsibility |
|----------|---------------|
| `build_deck(num_players, round_number, rng)` | Build and shuffle a multi-deck card set with `is_wild` flags. |
| `init_game(room_id, lobby_players, rng)` | Randomise seating, build `PlayerState` list, create initial `GameState`, deal round 1. |
| `_deal_round(gs, rng)` | Deal `round_number + 2` cards per player, set up piles, reset per-round fields. |
| `draw_from_pile(gs, player_id)` | Validate draw turn; move top of draw pile into hand; set `turn_phase = DISCARD`. |
| `draw_from_discard(gs, player_id)` | Same, but from discard pile. |
| `discard_card(gs, player_id, card_id)` | Validate discard turn; move card to discard pile; advance turn. |
| `attempt_go_out(gs, player_id, card_id)` | Validate discard phase; score remaining hand; if 0 penalty, discard and transition phase. |
| `score_hand(hand, wild_rank)` | Return total penalty points using exhaustive backtracking (`_best_partition`). |
| `_best_partition(hand, wild_rank)` | Recursive search over all set/run combinations to minimise penalty points. |
| `compute_round_results(gs)` | Score all hands; gone-out players get 0; update `cumulative_score`; return `List[RoundResult]`. |
| `advance_to_next_round(gs, rng)` | Increment round, rotate dealer, re-deal; set `phase = FINISHED` after round 11. |

### `backend/game/room_manager.py`

Stateful orchestration layer. The only mutable shared state in the application.

**Owns:**
- `rooms: Dict[str, RoomState]` — the 10 fixed room slots
- `room_connections: Dict[str, Dict[str, WebSocket]]` — active WebSocket connections per room
- `lobby_connections: Dict[str, WebSocket]` — active lobby-screen WebSocket connections
- `player_room_map: Dict[str, str]` — maps player ID to their current room
- `_cleanup_timers: Dict[str, asyncio.Task]` — per-room abandoned-room timers

**Connection lifecycle:**
- `join_room`: three cases — new player (→ `GATHERING`), reconnecting during `GATHERING` (updates WS), reconnecting during `IN_GAME` (replays `game_state` immediately).
- `leave_room` during `IN_GAME`: removes WebSocket only; game state is preserved for reconnect.

**Lobby flow:** `handle_join_lobby` / `handle_leave_lobby` manage the named-player list and broadcast `lobby_update`.

**Game lifecycle:**
- `handle_start_game`: validates ≥ 2 named players, calls `init_game`, broadcasts `game_starting` then per-player `game_state`.
- `handle_end_game`: broadcasts `lobby_reset`, then resets all room state to empty.

**In-game actions:** `handle_draw_card`, `handle_discard_card`, `handle_go_out`, `handle_next_round` — each calls the engine function and broadcasts updated state.

**Private view:** `_player_view(gs, viewer_id)` replaces opponent `hand` with `[]` + `hand_count`, and `draw_pile` with `[]` + `draw_pile_count`.

**Abandoned-room cleanup:** When all WebSocket connections drop during `IN_GAME`, a 300-second timer is scheduled. If no player reconnects before expiry, `_reset_room` is called automatically.

---

## 6. Data Models

### `Card`

```python
id: str        # "{rank}_{suit}_{deck_index}"  e.g. "king_hearts_0"
suit: Suit     # "hearts" | "diamonds" | "clubs" | "spades"
rank: Rank     # "ace" | "two" | ... | "king"
is_wild: bool  # True when rank == ROUND_WILD[round_number] at deck-build time
```

### `PlayerState`

```python
id: str
name: str
hand: List[Card]         # Populated only for the receiving player in client view
round_score: int         # Points from the current round (set at scoring time)
cumulative_score: int    # Running total across all completed rounds
has_gone_out: bool       # True once this player successfully goes out this round
```

### `RoundResult`

```python
player_id: str
player_name: str
round_points: int
cumulative_score: int
penalty_cards: List[Card]  # Cards that did not fit any combination
```

### `GameState`

```python
room_id: str
phase: GamePhase              # "playing" | "final_turns" | "scoring" | "finished"
turn_phase: TurnPhase         # "draw" | "discard"
players: List[PlayerState]    # Ordered; index determines turn order
dealer_index: int
current_player_index: int
draw_pile: List[Card]         # Hidden from clients (replaced with draw_pile_count)
discard_pile: List[Card]      # Visible; top card = discard_pile[-1]
round_number: int             # 1–11
wild_rank: Rank
gone_out_player_id: Optional[str]
final_turns_remaining: int
last_round_results: List[RoundResult]  # Populated at SCORING phase
next_round_confirmed_by: List[str]     # Player IDs who clicked "Next Round"
```

### `LobbyPlayer`

```python
id: str
name: str
```

### `RoomState`

```python
room_id: str          # "room-1" … "room-10"
room_name: str        # "Room 1" … "Room 10"
status: RoomStatus    # "empty" | "gathering" | "in_game"
player_count: int
player_ids: List[str]             # All WebSocket-connected players (named or unnamed)
lobby_players: List[LobbyPlayer]  # Only those who submitted a name
game_state: Optional[GameState]
max_players: int      # 8
min_players: int      # 2
```

### Key Constants

| Constant | Value |
|----------|-------|
| `ROUND_WILD` | Round 1 → `three`, …, Round 11 → `king` |
| `RANK_POINTS[ACE]` | 15 |
| `RANK_POINTS[2–10]` | Face value |
| `RANK_POINTS[J/Q/K]` | 10 |
| `decks_for_players(2–3)` | 1 deck |
| `decks_for_players(4–5)` | 2 decks |
| `decks_for_players(6–8)` | 3 decks |
| `NUM_ROOMS` | 10 |
| `ABANDON_TIMEOUT_SECONDS` | 300 |

---

## 7. WebSocket API

All messages are JSON objects with a `"type"` discriminator field.

### Lobby WebSocket — `/ws/lobby`

#### Server → Client

**`rooms_update`** — sent immediately on connect and after any room state change.
```json
{
  "type": "rooms_update",
  "rooms": [
    {
      "room_id": "room-1",
      "room_name": "Room 1",
      "status": "empty | gathering | in_game",
      "player_count": 0,
      "player_ids": [],
      "lobby_players": [],
      "game_state": null,
      "max_players": 8,
      "min_players": 2
    }
  ]
}
```

#### Client → Server (lobby)

Only keepalive pings. Server silently ignores them.
```json
{ "type": "ping" }
```

---

### Room WebSocket — `/ws/room/{room_id}?player_id=…`

#### Client → Server

| Message type | When sent | Key fields |
|---|---|---|
| `join_lobby` | Player submits display name | `room_id`, `player_name` |
| `leave_lobby` | Player returns to room list before game starts | `room_id` |
| `start_game` | Any named player triggers start (≥ 2 required) | `room_id` |
| `draw_card` | Active player draws | `room_id`, `source: "pile" \| "discard"` |
| `discard_card` | Active player discards | `room_id`, `card_id` |
| `go_out` | Active player attempts to go out | `room_id`, `card_id` |
| `next_round` | Player confirms readiness to advance | `room_id` |
| `end_game` | Any player triggers room reset | `room_id` |
| `ping` | Keepalive | — |

#### Server → Client

| Message type | When sent |
|---|---|
| `lobby_update` | On join and whenever named-player list changes |
| `game_starting` | Broadcast when game begins |
| `game_state` | Personalised; after every state change and on reconnect |
| `player_went_out` | Broadcast immediately when a player goes out |
| `round_over` | Broadcast when round reaches SCORING phase |
| `game_finished` | Broadcast after round 11 and all players confirm |
| `room_state` | When room metadata changes |
| `lobby_reset` | When `end_game` is called; triggers client navigation to lobby |
| `error` | Sent only to the client whose action was rejected |

**`game_state`** payload shape (personalised):
- Own `hand`: full `List[Card]`
- Opponent `hand`: `[]` + synthetic `hand_count: int`
- `draw_pile`: `[]` + synthetic `draw_pile_count: int`

**`player_went_out`** payload:
```json
{ "type": "player_went_out", "player_id": "uuid", "player_name": "Alice", "final_turns_remaining": 1 }
```

**`round_over`** payload:
```json
{
  "type": "round_over",
  "round_number": 1,
  "results": [
    { "player_id": "uuid", "player_name": "Alice", "round_points": 0, "cumulative_score": 0, "penalty_cards": [] }
  ]
}
```

**`game_finished`** payload:
```json
{
  "type": "game_finished",
  "leaderboard": [
    { "id": "uuid", "name": "Alice", "score": 12 }
  ]
}
```

---

## 8. Frontend

### Component Tree

```
App (phase state machine: 'lobby' | 'player_lobby' | 'game_room')
├── Lobby                  phase == 'lobby'
│   ├── RoomCard (×10)
│   └── RulesModal
├── PlayerLobby            phase == 'player_lobby'
│   └── RulesModal
└── GameRoom               phase == 'game_room'
    ├── CardView           one per card in local player's hand
    ├── PlayerSeat         one per opponent
    └── RulesModal
```

### Component Responsibilities

**`App`**
- Top-level phase state machine.
- Holds `selectedRoom` (`{ roomId, roomName }`) and `gameContext` (`{ roomId, roomName, players, myPlayerId, myName }`).
- Passes `handleSelectRoom`, `handleGameStarting`, `handleBackToLobby` callbacks to children.

**`Lobby`**
- Manages its own raw WebSocket to `/ws/lobby` with 3 s auto-reconnect and 30 s ping keepalive.
- Receives `rooms_update` and stores the room list in local state.
- Renders 10 `RoomCard` components in a grid.
- Calls `onSelectRoom(roomId)` for any non-`in_game` room click.

**`RoomCard`** (internal to `Lobby`)
- Purely presentational: room name, status badge, player count.

**`PlayerLobby`**
- Generates a stable `playerId` via `crypto.randomUUID()` on mount.
- Opens a raw WebSocket to `/ws/room/{roomId}?player_id={playerId}` with a one-time 500 ms retry guard for React StrictMode double-mount.
- Sends `join_lobby` on name submit, `leave_lobby` on back-navigation, `start_game` on button click.
- On `game_starting`: calls `onGameStarting` to transition to `GameRoom`.

**`GameRoom`**
- Opens a raw WebSocket to `/ws/room/{roomId}?player_id={myPlayerId}`.
- Renders one of three views based on `phase`:
  - **Active game** — pile area, opponent seats (`PlayerSeat`), own hand (`CardView`) with drag-to-reorder, action buttons (draw from pile, draw from discard, discard, go out).
  - **Round over** — scoring table with per-player results; "Next Round" / "See Final Scores" button.
  - **Game finished** — leaderboard ranked lowest to highest; "Back to Lobby" button.
- Persists hand card order to `localStorage` under key `hand-order-{playerId}-{roomId}`; merges server hand with stored order on each `game_state` update.
- Sends `draw_card`, `discard_card`, `go_out`, `next_round`, `end_game`.
- On `lobby_reset`, calls `onBackToLobby()`.

**`CardView`** (internal to `GameRoom`)
- Single card: suit/rank display, wild indicator, drag-and-drop handlers, selection highlight.

**`PlayerSeat`** (internal to `GameRoom`)
- Opponent view: name, cumulative score, card count (from `hand_count`).

**`RulesModal`**
- Fixed-position FAB ("📖 Rules") present on all three screens.
- Opens a scrollable modal with the full game rules as inline JSX.
- Closed via "X" button.

### UI Layout

The game screen is rendered from each player's own vantage point:
- **Current player** always shown at the bottom with their full hand.
- **Other players** arranged across the top in clockwise order; their cards are hidden (only card count shown).
- **Turn indicator**: ♦ diamond symbols ♦ surround the active player's name.
- **Round indicator**: current round number and wild card rank (e.g. "Round 3 — Wild: 5s").
- **Draw pile**: face-down stack.
- **Discard pile**: face-up stack showing only the top card.
- **Scores**: cumulative scores displayed for all players at all times.
- **"Go Out" message**: when a player goes out, all players see: _"🃏 [Player Name] has gone out! Each remaining player gets one final turn."_ This message persists while final turns are taken.
- **End of game**: final scores ranked from lowest (winner) to highest.

### WebSocket Management

All three main components (`Lobby`, `PlayerLobby`, `GameRoom`) manage their own raw `WebSocket` instances via `useRef`. The `useWebSocket.js` custom hook exists but is not used by any component.

---

## 9. Game Phase State Machine

### Room Status

```
empty ──join──→ gathering ──start_game──→ in_game ──end_game / timeout──→ empty
```

### `GamePhase` (server-side)

```
playing ──first go-out──→ final_turns ──all turns done──→ scoring ──all confirm──→ playing (next round)
                                                                                  └──after round 11──→ finished
```

### `TurnPhase` (server-side)

```
draw ──draw action──→ discard ──discard / go-out action──→ draw (next player)
```

### Frontend Phase (client-side, `App`)

```
'lobby' ──select room──→ 'player_lobby' ──game_starting──→ 'game_room'
                ↑                                                │
                └──────────── lobby_reset / back ───────────────┘
```

---

## 10. Deployment

| Attribute | Value |
|-----------|-------|
| Provider | Render.com |
| URL | https://three-thirteen.onrender.com |
| Container | Single Docker image (multi-stage: Node builds frontend, Python serves backend + static files) |
| Trigger | Automatic on push to `main` via GitHub integration |
| Health check | `GET /api/health` |
| WebSocket protocol | `wss://` in production |

Local development: `docker build -t three-thirteen . && docker run -p 8000:8000 three-thirteen` → http://localhost:8000

---

## 11. Test Coverage

### `test_engine.py` — pure engine unit tests

| Class | Coverage |
|---|---|
| `TestBuildDeck` | Deck size per player count, wild flags, all suits/ranks, shuffle randomness, unique card IDs |
| `TestInitGame` | Player count, cards per round, discard pile seeded, draw pile non-empty, initial phases, wild rank, first player |
| `TestDrawFromPile` / `TestDrawFromDiscard` | Hand/pile size changes, `turn_phase` transition, wrong-player and double-draw rejection |
| `TestDiscardCard` | Card moves to discard pile, turn advances, wrong `card_id` and must-draw-first rejections |
| `TestScoreHand` | Empty hand, valid combinations, unmatched cards, wilds in sets/runs, optimal partition, multi-deck duplicates, regression tests for wild prefix-slicing bug, run boundary cases, mixed-suit run invalidity, pure-wilds set, single wild |
| `TestAttemptGoOut` | Valid/invalid go-out, phase transitions, `final_turns_remaining`, wrong player, nonexistent card, wild combinations, second-player go-out scoring, gone-out player skipped in final turns, SCORING transition |
| `TestRoundResults` | Gone-out player scores 0, other players penalised, cumulative accumulation |
| `TestAdvanceToNextRound` | Round increment, wild rank update, dealer rotation, round 11 → `FINISHED`, card count per new round, `next_round_confirmed_by` cleared |
| `TestDecksForPlayers` | All threshold values |

### `test_rooms.py` — async `RoomManager` integration tests

| Class | Coverage |
|---|---|
| `TestInitialisation` | 10 rooms, correct IDs, all start empty |
| `TestLobbyConnections` | Immediate snapshot on connect, unregister, unknown ID safety |
| `TestJoinRoom` / `TestJoinRoomFailures` | Status transitions, player limits, duplicate ID, nonexistent room, `in_game` rejection |
| `TestLeaveRoom` | Player removal, last-player → empty, `IN_GAME` preservation |
| `TestGameLifecycle` / `TestStateTransitionSequence` | Full lifecycle, multi-room independence |
| `TestHandleJoinLobby` / `TestHandleLeaveLobby` | Named-player management, name trimming, broadcasts |
| `TestHandleStartGame` / `TestHandleEndGame` | Pre-conditions, broadcasts, room reset |
| `TestInGameReconnect` | StrictMode duplicate join, `IN_GAME` reconnect, stranger rejection, state preservation |
| `TestHandleNextRound` | Phase guards, partial/full confirmation, round 11 → `FINISHED`, idempotency |
| `TestAbandonedRoomCleanup` | Timer scheduling/cancellation, `_reset_room` correctness, room reuse after reset |

### `test_simulation.py` — end-to-end bot-driven simulations

- 40 parameterised test cases: `n_players ∈ {2, 3, 4, 5}` × `game_num ∈ 1..10`.
- Each simulates a full 11-round game with a deterministic seed.
- `_assert_invariants` checked after every single action: valid enums, in-bounds indices, no duplicate card IDs, card conservation.
- `_assert_round_end_invariants` checked after every round: SCORING phase, at least one gone-out player, gone-out scores 0, non-gone-out penalty scores match `score_hand`, `last_round_results` count.
- Final assertion: `phase == FINISHED` and `cumulative_score` matches manually accumulated total.

---

## 12. Known Dead Code

The following exist in the codebase but have no active code paths:

| Artifact | Status | Notes |
|---|---|---|
| `backend/game/events.py` | Unused | `EventBus`, `EventType`, `GameEvent`, `EventLogger` defined but never instantiated or imported in production. `EventLogger.log_event` is a no-op stub. |
| `frontend/src/hooks/useWebSocket.js` | Unused | Custom hook with reconnect, heartbeat, and message-queue infrastructure. All three main components manage WebSockets inline via `useRef` instead. |
| `frontend/src/components/Scoreboard.jsx` | Unused | Accepts `gameState` / `onPlayAgain` props but is never rendered. Body is mostly `# TODO` stubs; references `player.score` (not `cumulative_score`), suggesting it predates the current state model. |
| `app/` directory | Legacy | Early skeleton from before the `backend/` + `frontend/` restructure. Dead code. |

---

## 13. Post-v1 Backlog

_Items explicitly deferred to a future version. None of these are implemented today._

- Graphically rendered playing cards
- Animated card draws and discards
- Visual card grouping for sets and runs
- Table felt background and polished player avatars
- Sound effects
- Mobile-responsive layout
- Multiple ruleset selection in the Game Lobby
