import { http, HttpResponse } from 'msw'
import { setupServer } from 'msw/node'

import { API_URL } from '../api/client'
import type { EventItem, Page, Role, TokenResponse, User } from '../api/types'

/** Full URL of an API path, for MSW handlers. */
export function apiUrl(path: string): string {
  return `${API_URL}${path}`
}

export function makeUser(overrides: Partial<User> = {}): User {
  return {
    id: 'u-ana',
    email: 'ana@example.com',
    display_name: 'Ana',
    role: 'attendee',
    created_at: '2026-11-01T10:00:00Z',
    ...overrides,
  }
}

export function tokenResponse(user: User, token = 'access-1'): TokenResponse {
  return { access_token: token, token_type: 'bearer', expires_in: 900, user }
}

export function errorResponse(status: number, code: string, detail = code) {
  return HttpResponse.json({ detail, code }, { status })
}

/** Start signed in as a user with this role: the app-start refresh succeeds. */
export function signedInAs(role: Role, overrides: Partial<User> = {}): User {
  const user = makeUser({ role, ...overrides })
  server.use(http.post(apiUrl('/auth/refresh'), () => HttpResponse.json(tokenResponse(user))))
  return user
}

export function makeEvent(overrides: Partial<EventItem> = {}): EventItem {
  return {
    id: 'e-1',
    title: 'Jazz Night',
    slug: 'jazz-night',
    description: '<p>Live jazz.</p>',
    category: 'music',
    city: 'Novi Sad',
    venue: 'Studio M',
    address: null,
    starts_at: '2026-12-12T19:00:00Z',
    ends_at: '2026-12-12T22:00:00Z',
    capacity: 200,
    seats_taken: 162,
    seats_left: 38,
    price: 1500,
    tags: [],
    participants: [],
    image: null,
    status: 'published',
    organizer_id: 'u-org',
    organizer_name: 'Kulturni centar',
    rating_avg: 0,
    rating_count: 0,
    is_past: false,
    created_at: '2026-11-20T10:00:00Z',
    updated_at: '2026-11-20T10:00:00Z',
    ...overrides,
  }
}

export function eventsPage(items: EventItem[], total = items.length, page = 1): Page<EventItem> {
  return { items, total, page, page_size: 24 }
}

// By default every visitor is a guest: the refresh on app start answers 401.
export const server = setupServer(
  http.post(apiUrl('/auth/refresh'), () => errorResponse(401, 'NOT_AUTHENTICATED')),
  http.post(apiUrl('/auth/logout'), () => new HttpResponse(null, { status: 204 })),
  // The home page lists events; by default there are none.
  http.get(apiUrl('/events'), () => HttpResponse.json(eventsPage([]))),
  http.get(apiUrl('/events/cities'), () => HttpResponse.json([])),
  http.get(apiUrl('/events/tags'), () => HttpResponse.json([])),
)
