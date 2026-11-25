# Progress

Where the project stands. Update this file at the end of every work session and whenever a phase step is done. Phases are defined in [PROJECT_BRIEF.md](../PROJECT_BRIEF.md#10-phases).

## Status

| # | Phase | State |
| --- | --- | --- |
| 0 | Skeleton | Done |
| 1 | Auth and users | Done |
| 2 | Events | In progress |
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

## Phase 1: Auth and users (done)

1. [x] Domain errors and the `{"detail", "code"}` error body, user model, Argon2 password hashing, users index
2. [x] Register, login, access token, `/auth/me`
3. [x] Refresh token rotation with reuse detection, logout, two-tab concurrency test
4. [x] Roles, admin routes `GET /users` and `PATCH /users/{id}/role`, a test per role; scripts for demo users and the first admin
5. [x] Frontend: API client that refreshes once on 401, auth store, session check on start, sign in, sign up and sign out, route guards, permission matrix, admin users page

At the end: 134 backend tests, 127 frontend tests.

## Phase 2: Events (in progress)

1. [x] Event model and rules: create, edit, get by id and slug, statuses (draft, publish, cancel), delete, slugs with Serbian transliteration, ownership, indexes. 216 backend tests
2. [x] Event fields: tags, participants, rich text description sanitized on the server. 252 backend tests
3. [x] Public list: published only (cancelled stay readable by link), filters (category, tag, city, organizer, person, date, price, seats), `when=upcoming|past`, sort, pagination, `/events/cities`, `/events/tags`. 293 backend tests
4. [x] Frontend: home page grid (3, 4 or 6 columns) with filters in the URL, archive, event page; minimal typographic design. 153 frontend tests
5. [ ] Image upload pipeline: content check, resize, WebP, EXIF stripped, local storage and Cloudinary behind a protocol, placeholders. The Cloudinary keys are in the git-ignored root `.env`; copy them to `backend/.env` in this step
6. [ ] Frontend: organizer pages, my events, event form with rich text editor (h2 to h4), tags with suggestions, participants, image upload

## Next step

Phase 2, step 5: image upload pipeline (content check, resize, WebP, EXIF stripped), local storage and Cloudinary behind one protocol. Copy the Cloudinary keys from the root `.env` to `backend/.env`.

## Local environment

- MongoDB 9.0 Windows service, replica set `rs0`, `mongodb://localhost:27017/?replicaSet=rs0`.
- Python 3.14 through `uv`. Node 26 through nvm.
- Backend: `cd backend`, `uv run uvicorn app.main:create_app --factory --reload`.
- Demo accounts: `cd backend`, `uv run python -m scripts.seed_users --password <password>`.
- Frontend: `cd frontend`, `npm run dev`.
