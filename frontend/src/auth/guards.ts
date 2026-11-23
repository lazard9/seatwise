import { redirect } from '@tanstack/react-router'

import { useAuthStore } from '../store/auth'

/** For /login and /register: a signed-in user has nothing to do there. */
export function requireGuest(): void {
  if (useAuthStore.getState().status === 'signedIn') {
    throw redirect({ to: '/' })
  }
}
