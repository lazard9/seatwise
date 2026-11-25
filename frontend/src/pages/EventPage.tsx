import { useQuery } from '@tanstack/react-query'
import { getRouteApi, Link } from '@tanstack/react-router'
import DOMPurify from 'dompurify'
import { type ReactNode, useMemo } from 'react'

import { eventsKeys, getEventBySlug } from '../api/events'
import type { EventItem } from '../api/types'
import { EventArt } from '../components/events/EventArt'
import { FormError } from '../components/ui/FormError'
import { apiErrorCode, apiErrorMessage } from '../utils/apiErrors'
import { CATEGORY_NAMES, formatEventRange, formatEventStart, formatPrice } from '../utils/format'

const route = getRouteApi('/events/$slug')

// The same list the server keeps. The server is the real guard; this is a second one.
const DESCRIPTION_TAGS = [
  'p', 'br', 'h2', 'h3', 'h4', 'strong', 'em', 'u', 's', 'a', 'ul', 'ol', 'li', 'blockquote',
]

function cleanDescription(html: string): string {
  return DOMPurify.sanitize(html, { ALLOWED_TAGS: DESCRIPTION_TAGS, ALLOWED_ATTR: ['href', 'rel'] })
}

export function EventPage() {
  const { slug } = route.useParams()
  const query = useQuery({ queryKey: eventsKeys.bySlug(slug), queryFn: () => getEventBySlug(slug) })

  if (query.isPending) {
    return <p className="eyebrow">Loading event</p>
  }
  if (query.isError) {
    if (apiErrorCode(query.error) === 'EVENT_NOT_FOUND') {
      return (
        <section className="grid justify-items-start gap-3">
          <h1 className="display text-title">Event not found</h1>
          <p className="text-muted">It may have been removed, or the link is wrong.</p>
          <Link to="/" className="text-accent underline underline-offset-4">
            Back to upcoming events
          </Link>
        </section>
      )
    }
    return <FormError message={apiErrorMessage(query.error)} />
  }
  return <EventDetails event={query.data} />
}

function EventDetails({ event }: { event: EventItem }) {
  const description = useMemo(() => cleanDescription(event.description), [event.description])
  // Links from a past event lead into the archive, where its neighbours are.
  const listPath = event.is_past ? '/archive' : '/'
  const linkClass = 'text-ink underline decoration-rule underline-offset-4 hover:decoration-ink'

  return (
    <article className="grid gap-x-12 gap-y-8 lg:grid-cols-[minmax(0,7fr)_minmax(0,4fr)]">
      <div className="grid min-w-0 content-start gap-6">
        <div className="grid gap-2">
          <p className="eyebrow flex flex-wrap gap-x-3">
            <span>{CATEGORY_NAMES[event.category]}</span>
            <span>{formatEventStart(event.starts_at)}</span>
          </p>
          <h1 className="display text-title [overflow-wrap:anywhere]">{event.title}</h1>
        </div>

        <StatusNotice event={event} />

        <EventArt image={event.image} category={event.category} shape="wide" />

        <div
          className="event-description"
          // Cleaned twice: by the server before saving and by DOMPurify above.
          dangerouslySetInnerHTML={{ __html: description }}
        />

        {event.participants.length > 0 && (
          <section className="grid gap-3" aria-labelledby="participants-heading">
            <h2 id="participants-heading" className="display text-h2">
              Participants
            </h2>
            <ul className="flex flex-wrap gap-x-6 gap-y-2">
              {event.participants.map((person) => (
                <li key={`${person.key}-${person.role ?? ''}`}>
                  <Link to={listPath} search={{ person: person.key }} className={linkClass}>
                    {person.name}
                  </Link>
                  {person.role && <span className="eyebrow ml-2">{person.role}</span>}
                </li>
              ))}
            </ul>
          </section>
        )}
      </div>

      <aside className="min-w-0">
        <dl className="grid">
          <Fact label="When">{formatEventRange(event.starts_at, event.ends_at)}</Fact>
          <Fact label="Where">
            {event.venue}
            {event.address && (
              <>
                <br />
                {event.address}
              </>
            )}
            <br />
            <Link to={listPath} search={{ city: event.city }} className={linkClass}>
              {event.city}
            </Link>
          </Fact>
          <Fact label="Price">
            <span className={`tabular-nums ${event.price === 0 ? 'text-accent' : ''}`}>
              {formatPrice(event.price)}
            </span>
          </Fact>
          <Fact label="Seats">
            {event.seats_left === 0
              ? 'Sold out'
              : `${event.seats_left} of ${event.capacity} left`}
          </Fact>
          {event.organizer_name && (
            <Fact label="Organizer">
              <Link to={listPath} search={{ organizer: event.organizer_id }} className={linkClass}>
                {event.organizer_name}
              </Link>
            </Fact>
          )}
          {event.tags.length > 0 && (
            <Fact label="Tags">
              <span className="flex flex-wrap gap-x-3">
                {event.tags.map((tag) => (
                  <Link key={tag} to={listPath} search={{ tag }} className={linkClass}>
                    #{tag}
                  </Link>
                ))}
              </span>
            </Fact>
          )}
        </dl>
      </aside>
    </article>
  )
}

function Fact({ label, children }: { label: string; children: ReactNode }) {
  return (
    <div className="grid grid-cols-[6.5rem_minmax(0,1fr)] gap-3 border-b border-rule py-3">
      <dt className="eyebrow pt-0.5">{label}</dt>
      <dd className="text-body">{children}</dd>
    </div>
  )
}

function StatusNotice({ event }: { event: EventItem }) {
  if (event.status === 'cancelled') {
    return (
      <p role="status" className="border-l-2 border-accent pl-3 text-h3 text-accent">
        This event was cancelled.
      </p>
    )
  }
  if (event.status === 'draft') {
    return (
      <p role="status" className="border-l-2 border-ink pl-3 text-small">
        Draft. Only the organizer and admins can see this page.
      </p>
    )
  }
  if (event.is_past) {
    return <p className="eyebrow">This event has ended.</p>
  }
  return null
}
