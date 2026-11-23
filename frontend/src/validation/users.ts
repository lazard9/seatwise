import { z } from 'zod'

import { ROLES } from '../api/types'

export const SEARCH_MAX_LENGTH = 100

/** `/admin/users` search params. A bad value falls back to its default instead of an error. */
export const adminUsersSearchSchema = z.object({
  page: z.number().int().min(1).optional().catch(undefined),
  search: z.string().max(SEARCH_MAX_LENGTH).optional().catch(undefined),
  role: z.enum(ROLES).optional().catch(undefined),
})

export type AdminUsersSearch = z.infer<typeof adminUsersSearchSchema>

export const userFilterSchema = z.object({
  search: z.string().trim().max(SEARCH_MAX_LENGTH, `Use at most ${SEARCH_MAX_LENGTH} characters.`),
  role: z.union([z.enum(ROLES), z.literal('')]),
})

export type UserFilterValues = z.infer<typeof userFilterSchema>
