# Seatwise

An events platform. Organizers publish events; attendees discover them, reserve seats, save favorites, comment, and review events they attended.

The project is built around the problems the domain forces:

- **Capacity under concurrency:** two people cannot take the last seat.
- **Integrity across collections:** a reservation, its event's seat count, and a cancellation always agree.
- **Rules that depend on time and history:** you can review only an event you attended, after it ended.
- **Moderation:** comments written by one user, hidden by another.

> **Status:** phase 0, project setup. See [PROJECT_BRIEF.md](PROJECT_BRIEF.md) for the full specification and the phase plan.

## Stack

| Layer | Choice |
| --- | --- |
| Backend | Python 3.14, FastAPI, PyMongo (async), Pydantic, PyJWT, Argon2, Pillow, uv |
| Frontend | React, TypeScript, Vite, TanStack Router, TanStack Query, Zustand, React Hook Form, Zod, Tailwind CSS |
| Database | MongoDB 9.0 as a single-node replica set (transactions) |
| Tests | pytest + httpx, Vitest + Testing Library |
| Delivery | Docker Compose for production, GitHub Actions |

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
