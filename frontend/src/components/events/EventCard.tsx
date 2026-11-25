import { Link } from '@tanstack/react-router'

import type { EventItem } from '../../api/types'
import { formatEventStart, formatPrice } from '../../utils/format'
import type { Columns } from '../../validation/events'
import { EventArt } from './EventArt'

const TITLE_SIZE: Record<Columns, string> = {
  3: 'text-[1.3rem] leading-[1.12]',
  4: 'text-[1.15rem] leading-[1.15]',
  6: 'text-body leading-[1.2]',
}

/** One event in the grid. No box: the image, then type. The whole card is one link. */
export function EventCard({ event, columns }: { event: EventItem; columns: Columns }) {
  const soldOut = event.seats_left === 0
  return (
    <article className="group min-w-0">
      <Link
        to="/events/$slug"
        params={{ slug: event.slug }}
        className="grid content-start gap-2 text-ink no-underline"
      >
        <EventArt image={event.image} category={event.category} showLabel />
        <p className="eyebrow flex flex-wrap gap-x-3 gap-y-0.5">
          <span>{formatEventStart(event.starts_at)}</span>
          {soldOut && <span className="text-accent">Sold out</span>}
        </p>
        <h3
          className={`display ${TITLE_SIZE[columns]} [overflow-wrap:anywhere] group-hover:underline group-hover:decoration-1 group-hover:underline-offset-4`}
        >
          {event.title}
        </h3>
        {columns !== 6 && (
          <p className="text-small text-muted">
            {event.venue}, {event.city}
          </p>
        )}
        <p className={`text-small font-medium tabular-nums ${event.price === 0 ? 'text-accent' : ''}`}>
          {formatPrice(event.price)}
        </p>
      </Link>
    </article>
  )
}
