import { createFileRoute } from '@tanstack/react-router'

import { requireGuest } from '../auth/guards'
import { RegisterPage } from '../pages/RegisterPage'
import { authSearchSchema } from '../validation/auth'

export const Route = createFileRoute('/register')({
  validateSearch: authSearchSchema,
  beforeLoad: requireGuest,
  component: RegisterPage,
})
