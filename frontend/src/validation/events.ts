import { z } from 'zod'

import { CATEGORIES, EVENT_SORTS } from '../api/types'

export const COLUMN_CHOICES = [3, 4, 6] as const
export type Columns = (typeof COLUMN_CHOICES)[number]

/**
 * A text param. The router reads `?tag=2026` as the number 2026, so numbers are
 * turned back into text. A bad value is dropped instead of failing the page.
 */
function text(max: number) {
  return z
    .union([z.string(), z.number()])
    .transform(String)
    .pipe(z.string().trim().min(1).max(max))
    .optional()
    .catch(undefined)
}

/** Search params of `/` and `/archive`. Every filter lives in the URL. */
export const eventsSearchSchema = z.object({
  page: z.number().int().min(1).optional().catch(undefined),
  search: text(100),
  category: z.enum(CATEGORIES).optional().catch(undefined),
  tag: text(30),
  city: text(80),
  organizer: text(40),
  person: text(100),
  /** Calendar days, YYYY-MM-DD, in the visitor's time zone. */
  from: z.iso.date().optional().catch(undefined),
  to: z.iso.date().optional().catch(undefined),
  free: z.boolean().optional().catch(undefined),
  seats: z.boolean().optional().catch(undefined),
  sort: z.enum(EVENT_SORTS).optional().catch(undefined),
  cols: z
    .union([z.literal(3), z.literal(4), z.literal(6)])
    .optional()
    .catch(undefined),
})

export type EventsSearch = z.infer<typeof eventsSearchSchema>

export const eventSearchFormSchema = z.object({
  search: z.string().trim().max(100, 'Use at most 100 characters.'),
})

export type EventSearchFormValues = z.infer<typeof eventSearchFormSchema>
