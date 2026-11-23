import { redirect } from '@tanstack/react-router'

import type { Role } from '../api/types'
import { useAuthStore } from '../store/auth'

/** Thrown by a guard when the user is signed in but their role does not allow the page. */
export class ForbiddenError extends Error {
  constructor() {
    super('You do not have access to this page.')
    this.name = 'ForbiddenError'
  }
}

/** For /login and /register: a signed-in user has nothing to do there. */
export function requireGuest(): void {
  if (useAuthStore.getState().status === 'signedIn') {
    throw redirect({ to: '/' })
  }
}

/** Guests go to sign in, and come back to `href` afterwards. */
export function requireSignedIn(href: string): void {
  if (useAuthStore.getState().status !== 'signedIn') {
    throw redirect({ to: '/login', search: { redirect: href } })
  }
}

export function requireRole(roles: readonly Role[], href: string): void {
  requireSignedIn(href)
  const user = useAuthStore.getState().user
  if (!user || !roles.includes(user.role)) {
    throw new ForbiddenError()
  }
}
