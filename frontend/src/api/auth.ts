import { api } from './client'
import type { TokenResponse, User } from './types'

export interface LoginBody {
  email: string
  password: string
}

export interface RegisterBody extends LoginBody {
  display_name: string
}

export async function login(body: LoginBody): Promise<TokenResponse> {
  const { data } = await api.post<TokenResponse>('/auth/login', body, { skipAuthRefresh: true })
  return data
}

export async function register(body: RegisterBody): Promise<User> {
  const { data } = await api.post<User>('/auth/register', body, { skipAuthRefresh: true })
  return data
}

export async function logout(): Promise<void> {
  await api.post('/auth/logout', undefined, { skipAuthRefresh: true })
}

export async function getMe(): Promise<User> {
  const { data } = await api.get<User>('/auth/me')
  return data
}
