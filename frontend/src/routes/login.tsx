import { createFileRoute } from '@tanstack/react-router'

import { requireGuest } from '../auth/guards'
import { LoginPage } from '../pages/LoginPage'
import { authSearchSchema } from '../validation/auth'

export const Route = createFileRoute('/login')({
  validateSearch: authSearchSchema,
  beforeLoad: requireGuest,
  component: LoginPage,
})
