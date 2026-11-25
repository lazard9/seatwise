import type { EventItem } from '../../api/types'
import type { Columns } from '../../validation/events'
import { EventCard } from './EventCard'

// The chosen count applies on wide screens; phones and tablets get one to three.
const GRID: Record<Columns, string> = {
  3: 'grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-x-6 gap-y-10',
  4: 'grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-x-6 gap-y-10',
  6: 'grid-cols-2 md:grid-cols-3 lg:grid-cols-4 xl:grid-cols-6 gap-x-4 gap-y-8',
}

export function EventGrid({ events, columns }: { events: EventItem[]; columns: Columns }) {
  return (
    <div className={`grid ${GRID[columns]}`} data-testid="event-grid" data-columns={columns}>
      {events.map((event) => (
        <EventCard key={event.id} event={event} columns={columns} />
      ))}
    </div>
  )
}
