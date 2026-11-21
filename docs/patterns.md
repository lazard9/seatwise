# Patterns

Approaches this project follows, written as requirements. They describe what to build, not code to copy.

## Sessions: two tokens

- **Access token:** a short-lived JWT (15 minutes) returned in the login and refresh response body. The frontend keeps it in memory only, never in `localStorage`.
- **Refresh token:** a random string (not a JWT) in an `httpOnly`, `SameSite=Lax` cookie scoped to the auth path. `Secure` is configurable and on in production. Lifetime 7 days.
- The database stores only a SHA-256 hash of each refresh token, with `user_id`, `family_id`, `expires_at`, and when it was used or revoked. A TTL index on `expires_at` removes old rows.
- **Rotation:** every refresh marks the presented token as used and issues a new one in the same family.
- **Reuse detection:** presenting a token that was already rotated means it was copied, so the whole family is revoked and the user must sign in again.
- **Grace period:** a token reused within 10 seconds of its rotation is accepted, so two tabs refreshing at the same moment do not sign the user out. This needs a concurrency test.
- **Logout** revokes the current family only; other devices stay signed in.
- The role is read from the database on every request, never from the token, so role changes apply on the next request.

## Frontend session flow

- On app start, call refresh once. Success means signed in; failure means guest. Render guarded routes only after this check finishes.
- An API client interceptor adds the access token. On a 401 it refreshes once and retries the request once. Several requests failing at the same time share one refresh call. A failed refresh clears the session.
- The auth store (Zustand) is readable outside React, so the interceptor can use it.

## Errors

- Services raise domain exceptions with a stable `code`. One handler maps them to a status and `{"detail": "...", "code": "..."}`.
- The frontend branches on `code`, never on message text.

## Image uploads

- Check the file content (magic bytes), not its name or declared type. Accept JPEG, PNG and WebP up to a size limit. Return 413 and 415 for size and type, 400 for an empty or undecodable file.
- Decode with Pillow, apply the EXIF orientation, cap the longest side, save as WebP without metadata (removes GPS data). Reject very large pixel counts.
- Record each upload with its uploader and storage backend. A resource may use only images its owner uploaded, unless the caller is an admin.
- Delete a replaced image unless another resource still uses it. Delete uploads never attached to anything after a set time.
- Storage sits behind a small protocol with a local and a cloud implementation.

## Lists in the URL

- Search, filters, sort and page live in the URL, validated by a schema on the route, so a view can be shared, bookmarked and restored with Back.
- Every sort ends with `_id`, so equal values keep a stable order across pages.

## Slugs

- Made from the title: lowercase ASCII words joined by hyphens, Serbian Latin and Cyrillic transliterated. A taken slug gets `-2`, `-3`.
- Changing the title does not change the slug, so links keep working.
