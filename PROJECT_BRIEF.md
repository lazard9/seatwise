# Project Brief: Seatwise

Seatwise is an events platform. Repository: <https://github.com/lazard9/seatwise>.

This brief is the starting point for building the project. It defines the domain, data model, rules, API, permissions, and the order of work. Read it together with `CLAUDE.md`, which defines how the work is done.

---

## 1. Goal

A platform where organizers publish events and attendees discover them, reserve seats, save favorites, comment, and review events they attended.

The project is built from scratch. A reference project may be open alongside it for patterns (auth flow, upload pipeline, CI layout), but **no files are copied from it**. Every file in this repository is written for this domain.

The point of the project is the problems the domain forces:

- **Capacity under concurrency:** two people cannot take the last seat.
- **Integrity across collections:** a reservation, its event's seat count, and a cancellation must agree.
- **Rules that depend on time and history:** you can review only an event you attended, after it ended.
- **Moderation:** comments written by one user, hidden by another.

## 2. Stack

| Layer | Choice |
| --- | --- |
| Backend | Python 3.14, FastAPI, Uvicorn, Motor, Pydantic, PyJWT, Argon2, Pillow |
| Frontend | React, TypeScript, Vite, TanStack Router, TanStack Query, Zustand, React Hook Form, Zod, Tailwind CSS, Headless UI |
| Database | MongoDB 9.0, **run as a single-node replica set** in every environment |
| Tests | pytest + httpx (backend), Vitest + Testing Library (frontend) |
| Delivery | Dev: MongoDB installed locally as a replica set, no containers. Prod: Docker Compose (Nginx + API + DB). GitHub Actions |

**Why a replica set:** reservations change two collections at once (the reservation and the event's seat count). MongoDB transactions require a replica set, even with one node. Running it everywhere (dev, tests, CI, prod) means the transactional code is tested exactly as it runs.

## 3. Roles

| Role | Intent |
| --- | --- |
| `admin` | Everything, including user management and moderation of any content |
| `organizer` | Creates and manages their own events, moderates comments on them |
| `attendee` | Browses, reserves, favorites, comments, reviews. Default for new accounts |

The role is read from the database on every request, never from the token.

## 4. Data model

All collections store `_id` as ObjectId, serialized as string `id` in the API. All timestamps are UTC.

### users

| Field | Type | Notes |
| --- | --- | --- |
| email | string | unique, stored lowercased |
| password_hash | string | Argon2, never returned |
| display_name | string | shown on comments and reviews |
| role | enum | `admin`, `organizer`, `attendee` |
| created_at | datetime | |

### events

| Field | Type | Notes |
| --- | --- | --- |
| title | string | required, 3–120 chars |
| slug | string | unique, generated from title, transliterates Serbian Latin and Cyrillic |
| description | string | required |
| category | enum | `music`, `theatre`, `talk`, `workshop`, `sport`, `festival`, `other` |
| city | string | required |
| venue | string | required |
| address | string | optional |
| starts_at | datetime | required, in the future on create |
| ends_at | datetime | required, after `starts_at` |
| capacity | int | ≥ 1 |
| seats_taken | int | maintained by the backend only, never by the client |
| price | number | ≥ 0; 0 means free. Informational, no payments |
| image | string | upload URL or bundled placeholder |
| image_public_id | string | internal, never returned |
| status | enum | `draft`, `published`, `cancelled` |
| organizer_id | string | set from the caller on create, client value ignored |
| rating_avg | number | maintained by the backend, 0 when no reviews |
| rating_count | int | maintained by the backend |
| created_at, updated_at | datetime | |

Derived in responses (not stored): `seats_left`, `is_past`, `is_favorite` (for the signed-in caller), `my_reservation` (for the signed-in caller).

### reservations

| Field | Type | Notes |
| --- | --- | --- |
| event_id | string | |
| user_id | string | |
| seats | int | 1–6 per reservation |
| status | enum | `confirmed`, `cancelled` |
| created_at | datetime | |
| cancelled_at | datetime | null unless cancelled |
| cancelled_by | enum | `user`, `organizer`, `system` |

### reviews

| Field | Type | Notes |
| --- | --- | --- |
| event_id | string | |
| user_id | string | |
| rating | int | 1–5 |
| text | string | optional, max 2000 chars |
| created_at, updated_at | datetime | |

### favorites

| Field | Type | Notes |
| --- | --- | --- |
| user_id | string | |
| event_id | string | |
| created_at | datetime | |

### comments

| Field | Type | Notes |
| --- | --- | --- |
| event_id | string | |
| user_id | string | |
| parent_id | string | null for top level; replies are one level deep only |
| body | string | 1–1000 chars, plain text |
| status | enum | `visible`, `hidden` |
| hidden_by | string | user id of the moderator |
| edited_at | datetime | null unless edited |
| created_at | datetime | |

### refresh_tokens, uploads

Same purpose as in a standard two-token auth model and upload pipeline: hashed refresh tokens with family id and TTL index; upload records with URL, storage id, uploader, created_at.

## 5. Indexes

| Collection | Index | Purpose |
| --- | --- | --- |
| users | `email` unique | login, duplicate check |
| events | `slug` unique | links |
| events | `status, starts_at` | public listing of upcoming events |
| events | `city`, `category`, `organizer_id` | filters, "my events" |
| reservations | `event_id, user_id` unique, partial on `status: confirmed` | one active reservation per user per event |
| reservations | `user_id, created_at` | "my reservations" |
| reviews | `event_id, user_id` unique | one review per user per event |
| reviews | `event_id, created_at` | listing |
| favorites | `user_id, event_id` unique | toggle |
| comments | `event_id, created_at` | listing |
| refresh_tokens | `expires_at` TTL | automatic cleanup |

All indexes are created at application startup.

## 6. Business rules

### Events
- Only `published` events are visible publicly. Drafts are visible to their organizer and admins.
- `starts_at` must be in the future on create. `ends_at` must be after `starts_at`.
- `capacity` cannot be reduced below `seats_taken` (409).
- A past event cannot be edited except by admin.
- Cancelling an event sets `status: cancelled` and, in the same transaction, cancels all confirmed reservations with `cancelled_by: organizer`. Seats are not released (the event is gone).
- Deleting is admin only. An event with reservations cannot be deleted, only cancelled (409).

### Reservations
- Only for `published`, not started, not cancelled events.
- One confirmed reservation per user per event (unique partial index; violation returns 409).
- **Seat check is atomic.** Inside a transaction: conditional update on the event that increments `seats_taken` only if `seats_taken + seats <= capacity`, then insert the reservation. If the update matches nothing, return 409 "Not enough seats". A test fires concurrent reservations for the last seats and asserts the count never exceeds capacity.
- A user may cancel their reservation until the event starts. Cancellation releases seats in the same transaction.
- Organizers cannot reserve their own events.

### Reviews
- Allowed only if the user has a `confirmed` reservation for the event and the event has ended (`ends_at` in the past). Otherwise 403 with a clear message.
- One review per user per event (409 on duplicate). The author may edit or delete their own review.
- Creating, editing, or deleting a review recalculates `rating_avg` and `rating_count` on the event in the same transaction.
- Admin may delete any review.

### Favorites
- Toggle with PUT (add) and DELETE (remove). Both are idempotent and return 204.
- Any signed-in user, any published event, past or future.

### Comments
- Any signed-in user may comment on a published event.
- Replies are one level deep. A reply to a reply returns 422.
- The author may edit their comment; `edited_at` is set.
- The author may delete their comment. A deleted comment that has replies is replaced by a placeholder ("Comment deleted") so the thread keeps its shape; without replies it is removed.
- The event's organizer and admins may hide or unhide any comment on that event. Hidden comments are shown to moderators with a label, and to nobody else.

## 7. Permission matrix

| Action | Admin | Organizer | Attendee | Anonymous |
| --- | --- | --- | --- | --- |
| Browse published events | yes | yes | yes | yes |
| See drafts | all | own | no | no |
| Create event, upload image | yes | yes | no | no |
| Edit event | all | own | no | no |
| Cancel event | all | own | no | no |
| Delete event | yes | no | no | no |
| Reserve seats | yes | others' events | yes | no |
| Cancel own reservation | yes | yes | yes | no |
| See reservations for an event | all | own events | no | no |
| Review (after attending) | yes | others' events | yes | no |
| Favorite | yes | yes | yes | no |
| Comment | yes | yes | yes | no |
| Edit/delete own comment or review | yes | yes | yes | no |
| Hide/unhide comments | all | on own events | no | no |
| Manage users and roles | yes | no | no | no |

The backend enforces every row. The frontend mirrors the rules in one `permissions.ts` module, covered by tests for every role.

## 8. API

Prefix-free paths; behind Nginx they live under `/api`.

### Auth
| Method | Path | Notes |
| --- | --- | --- |
| POST | `/auth/register` | 201, role `attendee` |
| POST | `/auth/login` | access token in body, refresh cookie |
| POST | `/auth/refresh` | rotates cookie, returns access token |
| POST | `/auth/logout` | 204, revokes session family |
| GET | `/auth/me` | current user |

### Events
| Method | Path | Notes |
| --- | --- | --- |
| GET | `/events` | paginated; `search`, `city`, `category`, `date_from`, `date_to`, `min_price`, `max_price`, `free`, `has_seats`, `sort` (`soonest` default, `newest`, `price_asc`, `price_desc`, `rating_desc`), `mine`, `page`, `page_size` |
| GET | `/events/cities` | distinct cities for the filter |
| GET | `/events/{id}` | |
| GET | `/events/by-slug/{slug}` | |
| POST | `/events` | 201 |
| PUT | `/events/{id}` | |
| POST | `/events/{id}/publish` | draft → published |
| POST | `/events/{id}/cancel` | cancels event and its reservations |
| DELETE | `/events/{id}` | admin, only without reservations |

Every sort ends with `_id` as a tiebreaker. Past events are excluded by default; `include_past=true` includes them.

### Reservations
| Method | Path | Notes |
| --- | --- | --- |
| POST | `/events/{id}/reservations` | body `{seats}`; 201; 409 when full or already reserved |
| GET | `/events/{id}/reservations` | organizer of the event, admin |
| GET | `/me/reservations` | caller's reservations, upcoming first |
| POST | `/reservations/{id}/cancel` | owner, before start |

### Reviews
| Method | Path | Notes |
| --- | --- | --- |
| GET | `/events/{id}/reviews` | paginated, newest first |
| POST | `/events/{id}/reviews` | 201; 403 if not attended or not ended; 409 duplicate |
| PUT | `/reviews/{id}` | author |
| DELETE | `/reviews/{id}` | author or admin |

### Favorites
| Method | Path | Notes |
| --- | --- | --- |
| PUT | `/me/favorites/{event_id}` | 204, idempotent |
| DELETE | `/me/favorites/{event_id}` | 204, idempotent |
| GET | `/me/favorites` | paginated events |

### Comments
| Method | Path | Notes |
| --- | --- | --- |
| GET | `/events/{id}/comments` | top-level paginated, replies embedded |
| POST | `/events/{id}/comments` | 201; `parent_id` optional |
| PUT | `/comments/{id}` | author |
| DELETE | `/comments/{id}` | author or admin |
| POST | `/comments/{id}/hide`, `/comments/{id}/unhide` | organizer of the event, admin |

### Images, users
| Method | Path | Notes |
| --- | --- | --- |
| POST | `/images` | organizer, admin; content-sniffed, resized, WebP, EXIF stripped |
| GET | `/users` | admin |
| PATCH | `/users/{id}/role` | admin, not self |

### Status codes
| Code | When |
| --- | --- |
| 400 | malformed id, invalid state transition requested |
| 401 | missing, invalid, expired token |
| 403 | role or ownership does not allow it, or a rule (review before attending) blocks it |
| 404 | valid id, no document |
| 409 | conflict with current state: full event, duplicate reservation or review, capacity below seats taken, delete with reservations |
| 413, 415 | upload size, upload type |
| 422 | validation |

Error bodies have a stable shape: `{"detail": "...", "code": "EVENT_FULL"}` for domain errors, so the frontend can react to the code and not to the message text.

## 9. Frontend

| Route | Page | Access |
| --- | --- | --- |
| `/` | Upcoming events: search, filters, sort, pagination, all in the URL | public |
| `/events/:slug` | Event page: details, seats left, reserve, favorite, reviews, comments | public, actions need sign-in |
| `/me/reservations` | Upcoming and past reservations, cancel | signed in |
| `/me/favorites` | Saved events | signed in |
| `/organizer/events` | Own events incl. drafts, status, seats taken | organizer, admin |
| `/organizer/events/new`, `/organizer/events/:id/edit` | Event form with image upload | organizer, admin |
| `/organizer/events/:id/reservations` | Reservation list | organizer of the event, admin |
| `/admin/users` | Users and roles | admin |
| `/login`, `/register` | | guests |

Notes:
- All server data through TanStack Query, including edit pages. No `useEffect` fetching.
- Query keys nested by resource (`["events", ...]`, `["events", id, "comments"]`) so one invalidation refreshes related views.
- Reserve and favorite use optimistic updates with rollback on error. Reservation shows the backend's 409 message ("Not enough seats").
- Route-based code splitting from the start.
- Dark mode set before first paint by an inline script, so there is no flash.

## 10. Phases

Each phase ends with passing tests, lint, and build. Do not start the next phase with a red suite.

| # | Phase | Done when |
| --- | --- | --- |
| 0 | Skeleton | Repo, backend and frontend scaffolds, local Mongo replica set documented, `.env.example` files, CI running an empty test on both sides |
| 1 | Auth and users | Register, login, refresh rotation with reuse detection, logout, `/auth/me`, roles, admin user page. Tests for every token path |
| 2 | Events | CRUD, draft/publish/cancel, slug, filters, sort, pagination, indexes, URL state, image upload pipeline, placeholders |
| 3 | Reservations | Atomic seat check in a transaction, cancel, organizer list, "my reservations". Concurrency test |
| 4 | Favorites | Toggle, list, `is_favorite` in event responses, optimistic UI |
| 5 | Reviews | Eligibility rules, aggregates in a transaction, edit/delete |
| 6 | Comments | Threads, edit, delete with placeholder, moderation |
| 7 | Delivery | Production compose with Nginx, health checks, image build in CI, smoke test |
| 8 | Polish | Accessibility pass, empty and error states everywhere, README with screenshots |

## 11. Testing

- Backend integration tests run against a real MongoDB replica set in a separate test database. No database mocks.
- Every rule in section 6 has at least one test that proves it holds and one that proves it rejects.
- Every row of the permission matrix has a test per role.
- Concurrency tests for: last seats, double reservation by one user, simultaneous refresh in two tabs.
- Frontend: route guards, forms, list and URL state, reserve/favorite optimistic flows, comment thread rendering, permissions module.

## 12. Out of scope

Payments, email sending, password reset, waitlists, recurring events, maps, real-time updates. Each can be added later without changing the model above.
