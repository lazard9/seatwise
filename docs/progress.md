# Progress

Where the project stands. Update this file at the end of every work session and whenever a phase step is done. Phases are defined in [PROJECT_BRIEF.md](../PROJECT_BRIEF.md#10-phases).

## Status

| # | Phase | State |
| --- | --- | --- |
| 0 | Skeleton | Done |
| 1 | Auth and users | In progress |
| 2 | Events | Not started |
| 3 | Reservations | Not started |
| 4 | Favorites | Not started |
| 5 | Reviews | Not started |
| 6 | Comments | Not started |
| 7 | Reserved seating | Not started |
| 8 | Delivery | Not started |
| 9 | Polish | Not started |

## Phase 0: Skeleton (done)

- Docs: brief, conventions, decisions log.
- Backend: app factory, settings validated at startup, PyMongo async client, `/health`. 10 tests.
- Frontend: Vite, React, TypeScript, TanStack Router and Query, Tailwind, Vitest. 2 tests.
- CI: backend against MongoDB 9.0 replica set, frontend lint, test and build.

## Phase 1: Auth and users (in progress)

Steps, one or more commits each:

1. [ ] Domain errors and the `{"detail", "code"}` error body, user model, Argon2 password hashing, users index
2. [ ] Register, login, access token, `/auth/me`
3. [ ] Refresh token rotation with reuse detection, logout, two-tab concurrency test
4. [ ] Roles, admin routes `GET /users` and `PATCH /users/{id}/role`, a test per role
5. [ ] Frontend: auth store, API client with refresh on 401, login and register pages, route guards, admin users page

## Next step

Phase 1, step 1.

## Local environment

- MongoDB 9.0 Windows service, replica set `rs0`, `mongodb://localhost:27017/?replicaSet=rs0`.
- Python 3.14 through `uv`. Node 26 through nvm.
- Backend: `cd backend`, `uv run uvicorn app.main:create_app --factory --reload`.
- Frontend: `cd frontend`, `npm run dev`.
