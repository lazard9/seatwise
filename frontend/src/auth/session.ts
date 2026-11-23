import { logout } from '../api/auth'
import { refreshSession } from '../api/client'
import { useAuthStore } from '../store/auth'

let started: Promise<void> | null = null

/**
 * Restore the session from the refresh cookie, once per page load. The root
 * route awaits this, so guards never see the `unknown` state.
 */
export function ensureSession(): Promise<void> {
  started ??= refreshSession().then(() => undefined)
  return started
}

/** End the session on the server and here. Signing out never fails for the user. */
export async function signOut(): Promise<void> {
  try {
    await logout()
  } catch {
    // The server may be unreachable; the local session ends anyway.
  } finally {
    useAuthStore.getState().signedOut()
  }
}

export function resetSessionForTests(): void {
  started = null
}
