import { create } from 'zustand'

import type { TokenResponse, User } from '../api/types'

/** `unknown` until the first refresh on app start has answered. */
export type SessionStatus = 'unknown' | 'signedIn' | 'guest'

interface AuthState {
  status: SessionStatus
  user: User | null
  /** Kept in memory only, never in localStorage, so a script injected into the page cannot read it later. */
  accessToken: string | null
  signedIn: (session: TokenResponse) => void
  signedOut: () => void
}

const initialState = { status: 'unknown', user: null, accessToken: null } as const

/** Readable outside React (`useAuthStore.getState()`), so the API client and route guards use it too. */
export const useAuthStore = create<AuthState>()((set) => ({
  ...initialState,
  signedIn: (session) =>
    set({ status: 'signedIn', user: session.user, accessToken: session.access_token }),
  signedOut: () => set({ status: 'guest', user: null, accessToken: null }),
}))

export function resetAuthStore(): void {
  useAuthStore.setState(initialState)
}
