import { createFileRoute } from '@tanstack/react-router'

import { EventPage } from '../../pages/EventPage'

export const Route = createFileRoute('/events/$slug')({
  component: EventPage,
})
