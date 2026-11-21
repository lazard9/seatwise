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

## 2026-11-21: PyMongo async API instead of Motor

- **Decision:** The backend talks to MongoDB through `pymongo.AsyncMongoClient`.
- **Reason:** Motor is deprecated. MongoDB replaced it with the async API built into PyMongo, which supports sessions and transactions the same way.
- **Rejected:** Motor, as listed in the original brief.

## 2026-11-21: App factory, started with `--factory`

- **Decision:** `app.main.create_app(settings)` builds the app. There is no module-level `app`. Uvicorn runs it with `uvicorn app.main:create_app --factory`.
- **Reason:** Importing the module reads no settings and opens no connection, so tests build the app with their own settings and the test database.
- **Rejected:** A module-level `app = create_app()`, which would require a valid environment just to import the module.

## 2026-11-21: Frontend toolchain from the current Vite template

- **Decision:** Node 26 (`.nvmrc`), Vite 8, TypeScript 7 with `strict` and `noUncheckedIndexedAccess`, oxlint for linting, Tailwind CSS 4 through its Vite plugin, Vitest 5 with jsdom.
- **Reason:** These are what the official `create-vite` React TypeScript template ships today. oxlint replaces ESLint in that template and runs much faster.
- **Rejected:** ESLint (adds a slower second linter with no rule we need yet).

## 2026-11-21: Generated route tree is committed

- **Decision:** `frontend/src/routeTree.gen.ts` is committed and ignored by the linter.
- **Reason:** `npm run build` runs `tsc -b` before Vite, so the file must exist on a fresh checkout and in CI. The router plugin regenerates it whenever routes change.
- **Rejected:** Ignoring it in git and generating it in a separate step.

## 2026-11-21: Vitest runs through a small launcher

- **Decision:** `npm run test` calls `scripts/vitest.mjs`, which starts Vitest with the drive letter of the working directory in upper case.
- **Reason:** On Windows, a shell that starts in `d:\` makes Vitest load its own module twice, and every test file fails with "failed to find the current suite". Changing `root` or `setupFiles` in the config does not fix it. On Linux the launcher changes nothing.
- **Rejected:** Vitest globals (every future `import from 'vitest'` would still break), asking contributors to open the folder as `D:\`.

## 2026-11-21: Removed "pin limit" from the 409 list

- **Decision:** The status code table no longer lists a pin limit.
- **Reason:** Nothing in the events domain is pinned; the entry was left over from an earlier project.
- **Rejected:** Keeping it.
