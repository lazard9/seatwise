import { createFileRoute } from '@tanstack/react-router'

import { HomePage } from '../pages/HomePage'
import { eventsSearchSchema } from '../validation/events'

export const Route = createFileRoute('/')({
  validateSearch: eventsSearchSchema,
  component: HomePage,
})
