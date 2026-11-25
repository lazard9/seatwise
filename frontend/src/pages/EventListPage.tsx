import { keepPreviousData, useQuery } from '@tanstack/react-query'
import { Link, useSearch } from '@tanstack/react-router'

import { type EventListParams, eventsKeys, listCities, listEvents, popularTags } from '../api/events'
import { EventFilters, ColumnSwitch, type ListPath, SortSelect } from '../components/events/EventFilters'
import { EventGrid } from '../components/events/EventGrid'
import { FormError } from '../components/ui/FormError'
import { apiErrorMessage } from '../utils/apiErrors'
import { endOfDayIso, startOfDayIso } from '../utils/format'
import type { EventsSearch } from '../validation/events'

// Divides evenly by 3, 4 and 6, so every row of a full page is complete.
export const EVENTS_PAGE_SIZE = 24
const TAG_LIMIT = 12
// Cities and tags change rarely; there is no need to ask for them on every visit.
const FILTER_LISTS_STALE_MS = 5 * 60 * 1000

type When = 'upcoming' | 'past'

const PAGE: Record<When, { path: ListPath; title: string; noun: string; empty: string }> = {
  upcoming: {
    path: '/',
    title: 'Upcoming events',
    noun: 'upcoming event',
    empty: 'No upcoming events match these filters.',
  },
  past: {
    path: '/archive',
    title: 'Archive',
    noun: 'past event',
    empty: 'No past events match these filters.',
  },
}

function toParams(search: EventsSearch, when: When): EventListParams {
  return {
    page: search.page ?? 1,
    page_size: EVENTS_PAGE_SIZE,
    when,
    search: search.search,
    category: search.category,
    tag: search.tag,
    city: search.city,
    organizer: search.organizer,
    person: search.person,
    date_from: search.from ? startOfDayIso(search.from) : undefined,
    date_to: search.to ? endOfDayIso(search.to) : undefined,
    free: search.free,
    has_seats: search.seats,
    sort: search.sort,
  }
}

/** The home page (upcoming) and the archive (past): one list, two defaults. */
export function EventListPage({ when }: { when: When }) {
  const page = PAGE[when]
  const search: EventsSearch = useSearch({ from: page.path })
  const columns = search.cols ?? 3
  const params = toParams(search, when)

  const events = useQuery({
    queryKey: eventsKeys.list(params),
    queryFn: () => listEvents(params),
    // Keep the current page on screen while the next one loads.
    placeholderData: keepPreviousData,
  })
  const cities = useQuery({
    queryKey: eventsKeys.cities,
    queryFn: listCities,
    staleTime: FILTER_LISTS_STALE_MS,
  })
  const tags = useQuery({
    queryKey: eventsKeys.tags(TAG_LIMIT),
    queryFn: () => popularTags(TAG_LIMIT),
    staleTime: FILTER_LISTS_STALE_MS,
  })

  const items = events.data?.items ?? []
  // Names for the "Showing" line, read from the events that matched.
  const organizerName = search.organizer
    ? items.find((e) => e.organizer_id === search.organizer)?.organizer_name || undefined
    : undefined
  const personName = search.person
    ? items.flatMap((e) => e.participants).find((p) => p.key === search.person)?.name
    : undefined

  const total = events.data?.total ?? 0
  const totalPages = Math.max(1, Math.ceil(total / EVENTS_PAGE_SIZE))
  const defaultSort = when === 'upcoming' ? 'soonest' : 'latest'

  return (
    <section className="grid gap-8">
      <h1 className="display text-title">{page.title}</h1>

      <EventFilters
        from={page.path}
        search={search}
        cities={cities.data ?? []}
        tags={tags.data ?? []}
        organizerName={organizerName}
        personName={personName}
      />

      <div className="flex flex-wrap items-baseline justify-between gap-x-6 gap-y-3">
        <p className="eyebrow" aria-live="polite">
          {events.data ? `${total} ${page.noun}${total === 1 ? '' : 's'}` : 'Loading events'}
        </p>
        <div className="flex flex-wrap items-baseline gap-x-8 gap-y-3">
          <SortSelect from={page.path} value={search.sort ?? defaultSort} />
          <ColumnSwitch from={page.path} value={columns} />
        </div>
      </div>

      {events.isError && <FormError message={apiErrorMessage(events.error)} />}

      {events.data && items.length === 0 && (
        <div className="grid justify-items-start gap-3 py-10">
          <p className="text-h3">{page.empty}</p>
          <Link
            from={page.path}
            to="."
            search={{ cols: search.cols }}
            className="text-small text-accent underline underline-offset-4"
          >
            Clear filters
          </Link>
        </div>
      )}

      {items.length > 0 && <EventGrid events={items} columns={columns} />}

      {totalPages > 1 && (
        <nav
          aria-label="Pages"
          className="flex items-baseline justify-between border-t border-rule pt-4 font-mono text-small"
        >
          {params.page && params.page > 1 ? (
            <Link
              from={page.path}
              to="."
              search={(prev: EventsSearch) => ({ ...prev, page: (params.page ?? 1) - 1 })}
              className="text-ink underline underline-offset-4"
            >
              Previous
            </Link>
          ) : (
            <span />
          )}
          <span>
            Page {params.page} of {totalPages}
          </span>
          {(params.page ?? 1) < totalPages ? (
            <Link
              from={page.path}
              to="."
              search={(prev: EventsSearch) => ({ ...prev, page: (params.page ?? 1) + 1 })}
              className="text-ink underline underline-offset-4"
            >
              Next
            </Link>
          ) : (
            <span />
          )}
        </nav>
      )}
    </section>
  )
}
