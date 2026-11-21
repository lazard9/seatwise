# Decisions

Each entry records a choice the brief left open or changed: the date, the decision, why, and what was rejected.

## 2026-11-21: Project name is Seatwise

- **Decision:** The project and repository are named `seatwise`.
- **Reason:** The name points at the hardest problem in the domain: seats, capacity and concurrent reservations.
- **Rejected:** `events-app` (generic), `ld-events-app`.

## 2026-11-21: TanStack Router instead of React Router

- **Decision:** The frontend uses TanStack Router with file-based routes.
- **Reason:** The event list keeps search, filters, sort and page in the URL. TanStack Router validates search params with a schema and types them end to end, so invalid URLs are handled in one place. Route guards fit in `beforeLoad`, and loaders work together with TanStack Query.
- **Rejected:** React Router (search params are untyped strings). Next.js and other SSR frameworks (a second server next to FastAPI and a more complex cookie-based auth flow, for little gain in this project).

## 2026-11-21: MongoDB 9.0, installed locally without Docker

- **Decision:** Development uses MongoDB 9.0 installed as a Windows service and configured as the single-node replica set `rs0`. CI uses the `mongo:9.0` image started as a replica set. Docker Compose is used only for the production stack.
- **Reason:** The development machine has no Docker. A local replica set supports transactions exactly like the containerised one, so the transactional code is still tested as it runs.
- **Rejected:** Docker Desktop for development (needs WSL2 and disk space, adds nothing for a single database). MongoDB Atlas free tier (remote, slow for tests). MongoDB 7 from the original brief (9.0 is the current release and is what is installed).

## 2026-11-21: uv manages Python

- **Decision:** The backend uses `uv` for the Python version, the virtual environment and dependencies (`pyproject.toml` and `uv.lock`).
- **Reason:** One tool, reproducible lock file, fast installs locally and in CI.
- **Rejected:** `pip` with `requirements.txt` files.

## 2026-11-21: Removed "pin limit" from the 409 list

- **Decision:** The status code table no longer lists a pin limit.
- **Reason:** Nothing in the events domain is pinned; the entry was left over from an earlier project.
- **Rejected:** Keeping it.
