import { createRootRouteWithContext } from '@tanstack/react-router'

import { MainLayout } from '../components/layout/MainLayout'
import { NotFoundPage } from '../pages/NotFoundPage'
import type { RouterContext } from '../router'

export const Route = createRootRouteWithContext<RouterContext>()({
  component: MainLayout,
  notFoundComponent: NotFoundPage,
})
