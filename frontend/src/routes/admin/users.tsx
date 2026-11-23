import { createFileRoute } from '@tanstack/react-router'

import { AdminUsersPage } from '../../pages/AdminUsersPage'
import { adminUsersSearchSchema } from '../../validation/users'

export const Route = createFileRoute('/admin/users')({
  validateSearch: adminUsersSearchSchema,
  component: AdminUsersPage,
})
