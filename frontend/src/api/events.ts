import { api } from './client'
import type { Category, EventItem, EventSort, Page } from './types'

export interface EventListParams {
  page?: number | undefined
  page_size?: number | undefined
  search?: string | undefined
  category?: Category | undefined
  tag?: string | undefined
  city?: string | undefined
  organizer?: string | undefined
  person?: string | undefined
  date_from?: string | undefined
  date_to?: string | undefined
  free?: boolean | undefined
  has_seats?: boolean | undefined
  when?: 'upcoming' | 'past' | undefined
  sort?: EventSort | undefined
  mine?: boolean | undefined
}

export async function listEvents(params: EventListParams): Promise<Page<EventItem>> {
  const { data } = await api.get<Page<EventItem>>('/events', { params })
  return data
}

export async function getEventBySlug(slug: string): Promise<EventItem> {
  const { data } = await api.get<EventItem>(`/events/by-slug/${encodeURIComponent(slug)}`)
  return data
}

export async function listCities(): Promise<string[]> {
  const { data } = await api.get<string[]>('/events/cities')
  return data
}

export async function popularTags(limit: number): Promise<string[]> {
  const { data } = await api.get<string[]>('/events/tags', { params: { limit } })
  return data
}

/** Every events query starts with ['events'], so one invalidation refreshes them all. */
export const eventsKeys = {
  all: ['events'] as const,
  list: (params: EventListParams) => ['events', 'list', params] as const,
  bySlug: (slug: string) => ['events', 'slug', slug] as const,
  cities: ['events', 'cities'] as const,
  tags: (limit: number) => ['events', 'tags', limit] as const,
}
