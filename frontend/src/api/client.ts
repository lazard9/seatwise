import axios, { type InternalAxiosRequestConfig, isAxiosError } from 'axios'

import { useAuthStore } from '../store/auth'
import type { TokenResponse } from './types'

declare module 'axios' {
  interface AxiosRequestConfig {
    /** Auth routes answer 401 for their own reasons; never refresh and retry them. */
    skipAuthRefresh?: boolean
  }
}

interface RetriableConfig extends InternalAxiosRequestConfig {
  _retried?: boolean
}

export const API_URL: string = import.meta.env.VITE_API_URL ?? 'http://localhost:8000'

export const api = axios.create({
  baseURL: API_URL,
  // fetch in the browser and in tests alike; jsdom's XMLHttpRequest differs from browsers.
  adapter: 'fetch',
  // Sends the refresh cookie to /auth routes on another port of localhost.
  withCredentials: true,
})

api.interceptors.request.use((config) => {
  const token = useAuthStore.getState().accessToken
  if (token && !config.headers.has('Authorization')) {
    config.headers.set('Authorization', `Bearer ${token}`)
  }
  return config
})

let refreshing: Promise<boolean> | null = null

/**
 * Exchange the refresh cookie for a new access token. Resolves to whether the
 * user is signed in afterwards. Calls made while one is running share it, so
 * several requests failing together send a single refresh.
 */
export function refreshSession(): Promise<boolean> {
  refreshing ??= (async () => {
    try {
      const { data } = await api.post<TokenResponse>('/auth/refresh', undefined, {
        skipAuthRefresh: true,
      })
      useAuthStore.getState().signedIn(data)
      return true
    } catch {
      useAuthStore.getState().signedOut()
      return false
    } finally {
      refreshing = null
    }
  })()
  return refreshing
}

api.interceptors.response.use(undefined, async (error: unknown) => {
  if (!isAxiosError(error) || error.response?.status !== 401 || !error.config) {
    throw error
  }
  const config: RetriableConfig = error.config
  if (config.skipAuthRefresh || config._retried) {
    throw error
  }
  // Refresh once and retry once. A second 401 goes to the caller.
  config._retried = true
  if (!(await refreshSession())) {
    throw error
  }
  config.headers.set('Authorization', `Bearer ${useAuthStore.getState().accessToken}`)
  return api(config)
})
