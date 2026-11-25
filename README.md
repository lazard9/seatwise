# Seatwise

[![CI](https://github.com/lazard9/seatwise/actions/workflows/ci.yml/badge.svg)](https://github.com/lazard9/seatwise/actions/workflows/ci.yml)

An events platform. Organizers publish events; attendees discover them, reserve seats, save favorites, comment, and review events they attended.

The project is built around the problems the domain forces:

- **Capacity under concurrency:** two people cannot take the last seat.
- **Integrity across collections:** a reservation, its event's seat count, and a cancellation always agree.
- **Rules that depend on time and history:** you can review only an event you attended, after it ended.
- **Moderation:** comments written by one user, hidden by another.

> **Status:** phase 1 done: sign up, sign in with refresh rotation, sign out, roles and the admin users page. Phase 2 (events) in progress: create, edit, publish, cancel and delete work in the API. See [docs/progress.md](docs/progress.md) for where the work stands and [PROJECT_BRIEF.md](PROJECT_BRIEF.md) for the full specification.

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

### Users (admin only)

| Method | Path | Notes |
| --- | --- | --- |
| GET | `/users` | Newest first. Query: `page` (from 1), `page_size` (1 to 100, default 20), `role`, `search` (email or display name, ignores case). Returns `{items, total, page, page_size}` |
| PATCH | `/users/{id}/role` | Body `{role}`. 200 with the user. 403 `CANNOT_CHANGE_OWN_ROLE`, 404 `USER_NOT_FOUND`, 400 `INVALID_ID` |

Other roles get 403 `FORBIDDEN_ROLE`. A new role applies on the user's next request; their tokens stay valid.

### Events

| Method | Path | Notes |
| --- | --- | --- |
| GET | `/events` | Published events, one page (see below). `mine=true` lists the caller's own events in every status instead; 401 without sign-in |
| GET | `/events/cities` | Cities of published events, past ones included, in alphabetical order (Č sorts with C) |
| GET | `/events/tags` | Tags of published events, most used first. `limit` 1 to 100, default 50 |
| POST | `/events` | Organizer or admin. 201 with a `draft` owned by the caller. 422 `STARTS_IN_PAST` |
| GET | `/events/{id}` | 200 with the event. 404 `EVENT_NOT_FOUND`, 400 `INVALID_ID` |
| GET | `/events/by-slug/{slug}` | Same as above, by slug |
| PUT | `/events/{id}` | Replaces the editable fields. 403 `NOT_EVENT_OWNER` or `EVENT_PAST`, 409 `CAPACITY_BELOW_SEATS_TAKEN` or `EVENT_CANCELLED` |
| POST | `/events/{id}/publish` | Draft to published. 400 `INVALID_TRANSITION` |
| POST | `/events/{id}/cancel` | Cancels the event and its confirmed reservations. 400 `INVALID_TRANSITION` |
| DELETE | `/events/{id}` | Admin only. 204. 409 `EVENT_HAS_RESERVATIONS` |

Body for create and edit: `title` (3 to 120), `description` (HTML from the rich text editor, up to 20000 characters; see below), `category` (`music`, `theatre`, `talk`, `workshop`, `sport`, `festival`, `other`), `city`, `venue`, optional `address`, `starts_at` and `ends_at` with a UTC offset (end after start), `capacity` (1 to 100000), `price` in RSD (0 or more, 0 means free), `tags` (up to 10, each 2 to 30 characters; stored lowercased with spaces collapsed, duplicates dropped), `participants` (up to 20 of `{name, role}`; name 2 to 80, role optional, up to 40). The organizer, status, seats and ratings are set by the backend; such fields in the body are ignored.

Visibility: published and cancelled events are public, so a link to a cancelled event shows that it was cancelled. Drafts are visible only to their organizer and admins; for anyone else they are 404. Change rules:

- The organizer of the event and admins may edit, publish and cancel.
- After the event ends, only an admin may still change it.
- The slug comes from the title once, with Serbian Latin and Cyrillic transliterated (`Ђорђе` and `Đorđe` both give `djordje`). A taken slug gets `-2`, `-3`. Editing the title keeps the slug.

The description is cleaned on the server. It keeps `p`, `br`, `h2`, `h3`, `h4`, `strong`, `em`, `u`, `s`, `a` (http, https and mailto links only, with `rel="noopener noreferrer nofollow"`), `ul`, `ol`, `li` and `blockquote`. Scripts are removed with their content; other tags, `h1` included, are removed but their text stays. A description with no text left is 422.

Each participant in the response has a `key` made from the name the same way as slugs (`Đorđe Balašević` gives `djordje-balasevic`); the person filter will use it.

Query parameters of `GET /events`, all optional and combined with AND:

| Parameter | Meaning |
| --- | --- |
| `when` | `upcoming` (default): not yet ended, so running events stay listed. `past`: ended, for the archive |
| `sort` | `soonest` (default for upcoming), `latest` (default for past), `newest` (created), `price_asc`, `price_desc`, `rating_desc`. Each ends with `_id` |
| `search` | Up to 100 characters, matched literally and ignoring case in title, venue, city, the description text (not its markup), tags and participant names |
| `category`, `tag`, `city` | Exact values; `tag` is lowercased first. `city` takes a value from `/events/cities` |
| `organizer` | Organizer id. 400 `INVALID_ID` when malformed |
| `person` | A participant `key`, such as `djordje-balasevic` |
| `date_from`, `date_to` | Times with a UTC offset. An event is kept when it overlaps the range |
| `min_price`, `max_price`, `free` | Price range in RSD; `free=true` keeps only price 0 |
| `has_seats` | `true` keeps events with seats left |
| `page`, `page_size` | From 1; 1 to 100, default 20 |

Cancelled events are never listed, but stay readable by id and slug.

The response adds `seats_left`, `is_past` (true once `ends_at` has passed) and `organizer_name`. `image` is `null` until image uploads arrive.

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

Registration always creates an attendee. To get other roles (from `backend/`):

```bash
uv run python -m scripts.seed_users --password <password>          # admin@, organizer@, attendee@example.com
uv run python -m scripts.set_role --email you@example.com --role admin  # an account that already exists
```

### Frontend

Needs Node 26 (see `.nvmrc`; with nvm: `nvm install 26` and `nvm use 26`).

```bash
cd frontend
npm install
cp .env.example .env
npm run dev
```

App: <http://localhost:5173>. The backend must be running. Pages so far:

| Path | Who |
| --- | --- |
| `/` | everyone |
| `/login`, `/register` | guests; `?redirect=/path` returns there after signing in |
| `/admin/users` | admins: search, role filter, pages and role changes |

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
