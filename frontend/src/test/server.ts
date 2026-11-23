import { http, HttpResponse } from 'msw'
import { setupServer } from 'msw/node'

import { API_URL } from '../api/client'
import type { Role, TokenResponse, User } from '../api/types'

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

// By default every visitor is a guest: the refresh on app start answers 401.
export const server = setupServer(
  http.post(apiUrl('/auth/refresh'), () => errorResponse(401, 'NOT_AUTHENTICATED')),
  http.post(apiUrl('/auth/logout'), () => new HttpResponse(null, { status: 204 })),
)
