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

## 2026-11-21: Reserved seating is phase 7

- **Decision:** Choosing specific seats is added as phase 7, after comments. Delivery and polish move to phases 8 and 9. Until then events use general admission as in the brief.
- **Reason:** It fits the product and adds a second concurrency problem (seat holds that expire), but it depends on events and reservations working first. Keeping `seats` as a count and adding `seat_labels` later means phases 1 to 6 need no rework.
- **Rejected:** Building it into phase 3 (doubles the hardest phase), leaving it out.

## 2026-11-21: Account field rules

- **Decision:** Password 8 to 128 characters, no composition rules. Display name 2 to 50 characters after trimming. Email validated and stored lowercased; the unique index on `email` decides duplicates (409 `EMAIL_TAKEN`).
- **Reason:** The brief is silent. Length matters more than character classes (NIST SP 800-63B). The upper limit keeps Argon2 input bounded. Letting the index decide means two simultaneous sign-ups cannot both succeed.
- **Rejected:** Required digits or symbols, a find-then-insert duplicate check.

## 2026-11-21: Startup fails when MongoDB is unreachable

- **Decision:** The lifespan creates all indexes before the app accepts requests. If MongoDB cannot be reached, startup fails.
- **Reason:** The brief requires indexes at startup, and running without the unique indexes would let duplicates in. A failed start is visible at once; a process manager or Docker restarts it. `/health` still reports 503 if the database goes away later.
- **Rejected:** Starting without indexes and creating them later.

## 2026-11-21: Removed "pin limit" from the 409 list

- **Decision:** The status code table no longer lists a pin limit.
- **Reason:** Nothing in the events domain is pinned; the entry was left over from an earlier project.
- **Rejected:** Keeping it.

## 2026-11-21: Refresh rotation runs in a transaction

- **Decision:** One refresh reads the presented token, marks it used and inserts the next token in a single transaction. Every successful refresh writes the presented row, also inside the grace period. Revoking a family is a transaction too. Expected failures are returned from the transaction, not raised, and the family is revoked after it.
- **Reason:** Two refreshes of the same token, or a refresh racing a revocation, then write the same document. MongoDB lets only one commit and the driver reruns the other, which sees the new state. Without this, a token issued during a revocation could survive it. Raising inside the transaction would also roll back the revocation.
- **Rejected:** A find followed by separate writes (lost races), a lock collection (more moving parts for the same result).

## 2026-11-21: Refresh sessions slide, the grace period is 10 seconds

- **Decision:** Each refresh gives the new token a full 7 days, so an active user stays signed in. A rotated token is accepted again for 10 seconds; each such reuse gets its own next token in the same family. After that, reuse revokes the family.
- **Reason:** Tabs share one cookie, and two of them can send the same token before either sees the new one. The cost is that a copied token used within those 10 seconds is not detected; the brief asks for the grace period.
- **Rejected:** A fixed lifetime from sign-in (signs out active users every week), no grace period (the two-tab test fails: 4 of 5 tabs got 401).

## 2026-11-21: Refresh cookie details

- **Decision:** Cookie `seatwise_refresh`, path `/auth`, `HttpOnly`, `SameSite=Lax`, `Secure` from `REFRESH_COOKIE_SECURE`. A failed refresh clears it. Logout needs no access token and always returns 204.
- **Reason:** Path `/auth` keeps the cookie off every other API call. `SameSite=Lax` stops other sites from sending it with a POST, which covers CSRF for the two cookie routes. Logout must work after the access token has expired, and a page that signs out should never see an error.
- **Rejected:** Path `/auth/refresh` only (logout also needs the cookie), a CSRF token (not needed with `SameSite=Lax` and no state change on GET).

## 2026-11-23: One page shape for every list

- **Decision:** Paginated endpoints take `page` (from 1) and `page_size` (1 to 100, default 20) and return `{items, total, page, page_size}`. `GET /users` is the first; events, reviews and comments will use the same model.
- **Reason:** One shape means one frontend pager and one set of tests. Page numbers fit the brief, which puts `page` in the URL. The sort ends with `_id`, so equal timestamps never repeat or skip a row across pages.
- **Rejected:** Cursor pagination (no page numbers to show or share in a URL), a different shape per resource.

## 2026-11-23: Role changes and the last admin

- **Decision:** `PATCH /users/{id}/role` refuses the caller's own id (403 `CANNOT_CHANGE_OWN_ROLE`). An admin may change another admin. Setting the role a user already has returns 200. A role change does not end the user's sessions.
- **Reason:** The brief says "not self". It also means at least one admin always remains: the acting admin can never remove their own access. Sessions can stay because the role is read from the database on every request.
- **Rejected:** Counting admins before every change (the self rule already covers it), revoking sessions on a role change (not needed).

## 2026-11-23: Admin user search is a literal, case-insensitive match

- **Decision:** `search` on `GET /users` matches anywhere in the email or display name, ignoring case. The text is escaped before it goes into the regex, and limited to 100 characters.
- **Reason:** The admin page needs to find a person by part of a name. Escaping keeps `a.b` from matching `axb` and stops a caller from sending a costly pattern. The user count is small enough that a scan is fine.
- **Rejected:** A text index (word-based, so no partial matches), no search.

## 2026-11-23: Scripts for demo users and the first admin

- **Decision:** `scripts/seed_users.py` creates `admin@`, `organizer@` and `attendee@example.com` with a password given on the command line; running it again keeps passwords and restores the roles. `scripts/set_role.py` sets the role of an existing account by email.
- **Reason:** Registration always creates an attendee, so without a script nobody could become admin. The password is an argument so no known default password exists. `example.com` is reserved for examples and passes email validation.
- **Rejected:** An admin email in the environment that is promoted at startup (startup should not change data), a default demo password.

## 2026-11-23: Session check before any route renders

- **Decision:** The root route's `beforeLoad` awaits one refresh call per page load. Guards then read the Zustand store directly. The access token lives only in memory.
- **Reason:** The brief asks that guarded routes render only after the check. Doing it in the root route means every guard sees `signedIn` or `guest`, never `unknown`, and a reload on `/admin/users` stays there. Memory keeps the token away from scripts that read storage.
- **Rejected:** Rendering first and redirecting when the check finishes (a guest briefly sees a guarded page, an admin briefly sees the sign-in page), `localStorage` for the access token.

## 2026-11-23: Axios uses its fetch adapter; tests mock the API with MSW

- **Decision:** The API client is Axios with `adapter: 'fetch'`. Frontend tests run against MSW handlers, and a request with no handler fails the test.
- **Reason:** jsdom's `XMLHttpRequest` enforces CORS in its own way, so every mocked request failed as a network error. With fetch, tests and browsers take the same path. MSW tests the real client, interceptors included, instead of mocking our own modules.
- **Rejected:** Mocking `api/` modules with `vi.mock` (would not test the refresh logic), adding CORS headers to every mock.

## 2026-11-23: Sign-in redirects and the no-access page

- **Decision:** A guest on a guarded page goes to `/login?redirect=<path>` and returns there after signing in. The target must start with one `/`; anything else goes to `/`. A signed-in user without the role sees a "No access" page inside the normal layout. Signing up signs the user in at once.
- **Reason:** A `redirect` that accepts `//other.site` sends users to another site after they type their password (open redirect). Showing "No access" tells the user why, where a silent redirect home would look like a bug. Asking for the password twice after sign-up adds a step for nothing.
- **Rejected:** Redirecting a wrong role to `/`, a separate sign-in step after sign-up.

## 2026-11-23: Event states and who may change them

- **Decision:** A new event is always a draft. `publish` goes from draft to published only. `cancel` works from draft or published. Any other transition is 400 `INVALID_TRANSITION`. A cancelled event cannot be edited (409 `EVENT_CANCELLED`). An event counts as past once `ends_at` has passed; after that only an admin may edit, publish or cancel it (403 `EVENT_PAST`).
- **Reason:** Publishing as a separate step lets an organizer check the event before anyone sees it. Allowing cancel on a draft gives organizers a way to drop a draft, since delete is admin only. Using the end, not the start, as "past" keeps a running festival editable and listed.
- **Rejected:** A `status` field in the create body (two ways to publish), cancel from published only (a draft could never be removed by its organizer).

## 2026-11-23: Hidden events answer 404, cancelled events are hidden

- **Decision:** A draft or cancelled event is 404 `EVENT_NOT_FOUND` for anyone but its organizer and admins, the same as a missing event. Another organizer editing a published event they can see gets 403 `NOT_EVENT_OWNER`.
- **Reason:** The brief makes only published events public. A 403 would tell a stranger that a draft with that id or slug exists.
- **Open question:** attendees who had a reservation may want to open a cancelled event by its link and see that it was cancelled. Phase 3 can make cancelled events readable by link if wanted.

## 2026-11-23: Slugs are picked before insert and retried on a clash

- **Decision:** The slug is read from the title with Serbian transliteration, cut to 80 characters at a word boundary, and falls back to `event`. The service reads the taken `base` and `base-N` slugs, picks the first free one, and inserts. If the unique index rejects it because another create won, it picks again (up to 10 times).
- **Reason:** The unique index is the only check that holds under concurrency. A test creates five events with one title at once and gets five slugs; with one attempt it fails.
- **Rejected:** A random suffix (ugly links), a counter collection (one more collection for a rare race).

## 2026-11-23: Edits check their conditions in the write itself

- **Decision:** `PUT /events/{id}` replaces all editable fields. The update filter requires `seats_taken <= capacity` and a status other than cancelled, so a reservation or a cancel that lands after the first read cannot be overwritten. When the filter misses, the service reads again to return the right code.
- **Reason:** Checking capacity in Python and then writing leaves a gap where a reservation can push `seats_taken` above the new capacity.
- **Rejected:** A transaction for a single-document update (the conditional write is enough).

## 2026-11-23: Cancel and delete run in transactions with reservations

- **Decision:** Cancel sets the event to cancelled and its confirmed reservations to cancelled with `cancelled_by: organizer` in one transaction. Seats are not released. Delete is admin only and refuses an event with any reservation, confirmed or cancelled (409 `EVENT_HAS_RESERVATIONS`); the check and the delete share one transaction.
- **Reason:** The brief requires cancel to be atomic. Cancelled reservations are history that points at the event, so deleting it would leave them dangling. A reservation commit also writes the event, so it conflicts with a delete in progress and one of the two is retried.
- **Rejected:** Allowing delete when only cancelled reservations remain (breaks "my reservations" history).

## 2026-11-23: Event input details

- **Decision:** Times must carry a UTC offset; a time without one is 422. They are stored in UTC. `price` is rounded to two decimals, capped at 1000000; `capacity` is capped at 100000. A blank `address` is stored as missing. `starts_at` in the past on create is 422 `STARTS_IN_PAST`; on edit it is not checked.
- **Reason:** A time without an offset could mean any zone. The caps stop typing mistakes. The brief asks for a future start only on create, and an admin must be able to fix a past event.
- **Rejected:** Assuming Europe/Belgrade for times without an offset.
