# Seatwise

[![CI](https://github.com/lazard9/seatwise/actions/workflows/ci.yml/badge.svg)](https://github.com/lazard9/seatwise/actions/workflows/ci.yml)

An events platform. Organizers publish events; attendees discover them, reserve seats, save favorites, comment, and review events they attended.

The project is built around the problems the domain forces:

- **Capacity under concurrency:** two people cannot take the last seat.
- **Integrity across collections:** a reservation, its event's seat count, and a cancellation always agree.
- **Rules that depend on time and history:** you can review only an event you attended, after it ended.
- **Moderation:** comments written by one user, hidden by another.

> **Status:** phase 1 in progress. Register, login, refresh rotation and logout are done; admin user routes and the frontend sign-in come next. See [docs/progress.md](docs/progress.md) for where the work stands and [PROJECT_BRIEF.md](PROJECT_BRIEF.md) for the full specification.

## Stack

| Layer | Choice |
| --- | --- |
| Backend | Python 3.14, FastAPI, PyMongo (async), Pydantic, PyJWT, Argon2, Pillow, uv |
| Frontend | React, TypeScript, Vite, TanStack Router, TanStack Query, Zustand, React Hook Form, Zod, Tailwind CSS |
| Database | MongoDB 9.0 as a single-node replica set (transactions) |
| Tests | pytest + httpx, Vitest + Testing Library |
| Delivery | Docker Compose for production, GitHub Actions |

## API

Interactive docs: <http://localhost:8000/docs>. Errors from business rules have a stable body, `{"detail": "...", "code": "..."}`; clients branch on `code`.

### Auth

| Method | Path | Notes |
| --- | --- | --- |
| POST | `/auth/register` | Body `{email, password, display_name}`. 201 with the user; role is always `attendee`. 409 `EMAIL_TAKEN` |
| POST | `/auth/login` | Body `{email, password}`. 200 with `access_token` (15 minutes), `expires_in` and the user, and sets the refresh cookie. 401 `INVALID_CREDENTIALS` |
| POST | `/auth/refresh` | No body; reads the refresh cookie. 200 with a new access token and the user, and replaces the cookie. 401 `NOT_AUTHENTICATED`, `INVALID_REFRESH_TOKEN` or `REFRESH_TOKEN_REUSED`, and clears the cookie |
| POST | `/auth/logout` | 204. Ends this session only (other devices stay signed in) and clears the cookie. Needs no access token |
| GET | `/auth/me` | The signed-in user. Needs `Authorization: Bearer <token>` |

401 codes for the access token: `NOT_AUTHENTICATED` (no token), `INVALID_TOKEN`, `TOKEN_EXPIRED`. The role is read from the database on every request, never from the token.

The refresh token lives in the `seatwise_refresh` cookie: `HttpOnly`, `SameSite=Lax`, path `/auth`, 7 days, `Secure` when `REFRESH_COOKIE_SECURE=true`. Each refresh replaces it. A replaced token sent again more than 10 seconds later means it was copied, so that session is closed. Clients call `/auth/refresh` on start to restore a session, and again when the access token expires.

Field rules: email is stored lowercased; password 8 to 128 characters; display name 2 to 50 characters.

### Health

| Method | Path | Notes |
| --- | --- | --- |
| GET | `/health` | 200 when MongoDB answers, 503 when it does not |

## Documentation

- [PROJECT_BRIEF.md](PROJECT_BRIEF.md): domain, data model, rules, API, permissions and phases
- [CLAUDE.md](CLAUDE.md): conventions and the definition of done
- [docs/decisions.md](docs/decisions.md): decisions and the reasons behind them

## Getting started

### Prerequisites

- [uv](https://docs.astral.sh/uv/) (installs Python 3.14 for the project)
- MongoDB 9.0 running as a single-node replica set. Transactions need a replica set, even with one node:
  1. In `mongod.cfg` add:
     ```yaml
     replication:
       replSetName: rs0
     ```
  2. Restart the MongoDB service, then run once in `mongosh`:
     ```js
     rs.initiate({ _id: "rs0", members: [{ _id: 0, host: "localhost:27017" }] })
     ```

### Backend

```bash
cd backend
uv sync                      # creates .venv with Python 3.14 and all dependencies
cp .env.example .env         # then set JWT_SECRET (the command is in the file)
uv run uvicorn app.main:create_app --factory --reload
```

- API: <http://localhost:8000>
- Swagger UI: <http://localhost:8000/docs>
- Health check: <http://localhost:8000/health>

The app refuses to start without a `JWT_SECRET` of at least 32 bytes.

### Frontend

Needs Node 26 (see `.nvmrc`; with nvm: `nvm install 26` and `nvm use 26`).

```bash
cd frontend
npm install
cp .env.example .env
npm run dev
```

App: <http://localhost:5173>

### Tests and lint

```bash
cd backend
uv run pytest -q
uv run ruff check .
uv run ruff format --check .

cd ../frontend
npm run test
npm run lint
npm run build
```

Backend tests use the `seatwise_test` database on `mongodb://localhost:27017/?replicaSet=rs0` and drop it when they finish. Set `MONGODB_URL` to use another server. They never read `.env`.

## License

MIT. See [LICENSE](LICENSE).
