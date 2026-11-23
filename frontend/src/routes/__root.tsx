import { createRootRouteWithContext } from '@tanstack/react-router'

import { ensureSession } from '../auth/session'
import { MainLayout } from '../components/layout/MainLayout'
import { NotFoundPage } from '../pages/NotFoundPage'
import type { RouterContext } from '../router'

export const Route = createRootRouteWithContext<RouterContext>()({
  // Every route waits for the session check, so guards know who is signed in.
  beforeLoad: () => ensureSession(),
  component: MainLayout,
  notFoundComponent: NotFoundPage,
})
