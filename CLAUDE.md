# CLAUDE.md

Instructions for the agent working on this repository. Read `PROJECT_BRIEF.md` before any task; it is the source of truth for the domain, rules, API, and phases.

At the start of a session read `docs/progress.md` to see where the work stands, and update it when a step is done. `docs/patterns.md` describes the approaches for auth, errors, uploads, URL state and slugs.

## 1. Workspace

- This repository is a new project. Everything in it is written for the events domain.
- A reference project may be open in the same workspace. It is **read-only** and not needed: `docs/patterns.md` describes the patterns to follow.
- **Never copy, move, or rename files from the reference project.** Never paste code from it. Write each file fresh for this domain, using the brief as the specification.
- If a task seems to need something from the reference project, describe the pattern in your own words and implement it from scratch.
- Local development runs without Docker. MongoDB 9.0 runs as a Windows service configured as the single-node replica set `rs0`. Connection string: `mongodb://localhost:27017/?replicaSet=rs0`. Docker is used only for the production compose file and in CI.
- Python is managed with `uv`. Node and npm for the frontend.

## 2. How to work

- Work phase by phase as listed in the brief. Do not start the next phase while tests, lint, or build fail.
- Before writing code for a feature, state in a few lines which files you will create or change and why.
- Keep each change to one concern. Separate refactors from features.
- When the brief is silent or ambiguous, choose the smaller option, implement it, and record the decision in `docs/decisions.md` (date, decision, reason, alternative rejected).
- When a rule in the brief seems wrong, say so before implementing it. Do not silently deviate.
- Write tests together with the feature, not after it.

## 3. Backend conventions

Structure:

```
backend/
├── app/
│   ├── main.py            app factory, lifespan, routers
│   ├── config.py          settings from environment, validated at startup
│   ├── database/          client, get_database, dependencies, indexes, transactions helper
│   ├── auth/              tokens, passwords, dependencies (current user, roles, optional user)
│   ├── models/            Pydantic request/response models per resource
│   ├── services/          business logic per resource
│   ├── routes/            HTTP only: parse, call service, map errors
│   └── storage/           image storage protocol, local and cloud implementations
├── tests/
│   ├── unit/
│   └── integration/
└── scripts/               seed_users.py, seed.py
```

Rules:

- Layers: route → dependency → service → collection. Routes know HTTP, services do not.
- Services receive collections (or the database and a session) as arguments. No module-level collections, no import-time clients.
- Services raise domain exceptions (`NotFound`, `Forbidden`, `Conflict` with a `code`). One exception handler maps them to HTTP status and the `{"detail", "code"}` body.
- Any operation that changes more than one collection runs in a transaction through a shared helper.
- Identifiers: parse strings to ObjectId in the service; invalid id raises a domain error mapped to 400.
- Serialization: explicit serializer per resource; internal fields (`password_hash`, `image_public_id`) never leave the service.
- Ownership fields (`organizer_id`, `user_id`) are always set from the caller, never from the request body.
- Timestamps are timezone-aware UTC.
- Configuration only through environment variables, validated at startup. The app refuses to start on a missing or weak secret.
- Every sort includes `_id` as the last key.
- Type hints everywhere. Format with `ruff format`, lint with `ruff check`.

## 4. Frontend conventions

Structure:

```
frontend/src/
├── api/          one module per resource, one function per endpoint
├── components/   ui/ (generic), plus folders per domain (events, reservations, reviews, comments)
├── pages/
├── routes/       TanStack Router file routes, guards in beforeLoad, search param schemas
├── store/        auth store (Zustand)
├── hooks/
├── utils/        permissions, formatters, search params, api errors
├── validation/   Zod schemas
└── test/         setup, renderWithProviders, helpers
```

Rules:

- Components never call Axios. All HTTP goes through `api/`.
- All server data through TanStack Query. No fetching in `useEffect`.
- URL search params are validated by a Zod schema on the route (`validateSearch`). Components read them through the router, never by parsing `location.search`.
- After a mutation, invalidate the narrowest query keys that are affected.
- Forms use React Hook Form with a Zod schema. Zod rules mirror Pydantic rules; the backend stays authoritative.
- Branch on error `code` from the API, not on message text.
- `utils/permissions.ts` mirrors the permission matrix. UI hides what a role cannot do; it never replaces backend checks.
- Every interactive element is reachable by keyboard and has a visible focus state. Every input has a label.
- Strict TypeScript. No `any` without a comment explaining why.

## 5. Testing rules

- Backend integration tests use a real MongoDB replica set and a separate test database. Never mock the database.
- Each business rule gets a passing-case test and a rejecting-case test.
- Each permission matrix row gets a test per role.
- Concurrency-sensitive code (seats, refresh rotation) gets a concurrency test.
- Frontend tests render through `renderWithProviders` with a fresh QueryClient and retries off.
- A bug fix starts with a failing test that reproduces it.

## 6. Definition of done

A task is done when:

1. Backend (from `backend/`): `uv run pytest -q` passes, `uv run ruff check .` and `uv run ruff format --check .` are clean.
2. Frontend: `npm run test`, `npm run lint`, and `npm run build` pass.
3. New behavior is covered by tests as described above.
4. API changes are reflected in the README API section.
5. Non-obvious decisions are recorded in `docs/decisions.md`.
6. No secrets, `.env` files, or generated media are committed.

## 7. Commits

- Conventional prefixes: `feat:`, `fix:`, `test:`, `refactor:`, `docs:`, `chore:`, `ci:`.
- One logical change per commit. The message says what changed and, when not obvious, why.
- No AI attribution: no `Co-Authored-By` trailer for an assistant and no "Generated with" line in commits or pull requests. The author credits the tools himself.

## 8. Writing

- Documentation and comments in plain English, short sentences, concrete statements.
- No em dashes in docs and UI copy.
- Comments explain why, not what. Do not leave commented-out code.
