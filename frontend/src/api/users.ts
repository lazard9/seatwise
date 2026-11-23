import { api } from './client'
import type { Page, Role, User } from './types'

export interface UserListParams {
  page?: number | undefined
  page_size?: number | undefined
  role?: Role | undefined
  search?: string | undefined
}

export async function listUsers(params: UserListParams): Promise<Page<User>> {
  const { data } = await api.get<Page<User>>('/users', { params })
  return data
}

export async function changeRole(userId: string, role: Role): Promise<User> {
  const { data } = await api.patch<User>(`/users/${encodeURIComponent(userId)}/role`, { role })
  return data
}

/** Every users query starts with this key, so one invalidation refreshes them all. */
export const usersKeys = {
  all: ['users'] as const,
  list: (params: UserListParams) => ['users', 'list', params] as const,
}
