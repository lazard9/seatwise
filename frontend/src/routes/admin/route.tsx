import { createFileRoute } from '@tanstack/react-router'

import { requireRole } from '../../auth/guards'

// Every page under /admin is for admins only.
export const Route = createFileRoute('/admin')({
  beforeLoad: ({ location }) => requireRole(['admin'], location.href),
})
