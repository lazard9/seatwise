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

export const CATEGORIES = [
  'music',
  'theatre',
  'talk',
  'workshop',
  'sport',
  'festival',
  'other',
] as const
export type Category = (typeof CATEGORIES)[number]

export const EVENT_STATUSES = ['draft', 'published', 'cancelled'] as const
export type EventStatus = (typeof EVENT_STATUSES)[number]

export const EVENT_SORTS = [
  'soonest',
  'latest',
  'newest',
  'price_asc',
  'price_desc',
  'rating_desc',
] as const
export type EventSort = (typeof EVENT_SORTS)[number]

export interface Participant {
  name: string
  role: string | null
  /** Made from the name; the person filter uses it. */
  key: string
}

export interface EventItem {
  id: string
  title: string
  slug: string
  /** HTML, cleaned by the server. Clean it again before rendering. */
  description: string
  category: Category
  city: string
  venue: string
  address: string | null
  starts_at: string
  ends_at: string
  capacity: number
  seats_taken: number
  seats_left: number
  /** In RSD; 0 means free. */
  price: number
  tags: string[]
  participants: Participant[]
  image: string | null
  status: EventStatus
  organizer_id: string
  organizer_name: string
  rating_avg: number
  rating_count: number
  is_past: boolean
  created_at: string
  updated_at: string
}
