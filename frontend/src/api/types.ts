// Shapes of the backend API. Field names follow the API (snake_case) on purpose,
// so a response can be used as it arrives.

export const ROLES = ['admin', 'organizer', 'attendee'] as const
export type Role = (typeof ROLES)[number]

export interface User {
  id: string
  email: string
  display_name: string
  role: Role
  created_at: string
}

export interface TokenResponse {
  access_token: string
  token_type: 'bearer'
  expires_in: number
  user: User
}

export interface Page<T> {
  items: T[]
  total: number
  page: number
  page_size: number
}

/** Body of every domain error. Branch on `code`, never on `detail`. */
export interface ApiErrorBody {
  detail: string
  code: string
}
