import { createFileRoute } from '@tanstack/react-router'

import { ArchivePage } from '../pages/ArchivePage'
import { eventsSearchSchema } from '../validation/events'

export const Route = createFileRoute('/archive')({
  validateSearch: eventsSearchSchema,
  component: ArchivePage,
})
