import { zodResolver } from '@hookform/resolvers/zod'
import { Link, useNavigate } from '@tanstack/react-router'
import type { ReactNode } from 'react'
import { useForm } from 'react-hook-form'

import { CATEGORIES, EVENT_SORTS, type EventSort } from '../../api/types'
import { CATEGORY_LABELS } from '../../utils/format'
import {
  COLUMN_CHOICES,
  type EventSearchFormValues,
  type EventsSearch,
  eventSearchFormSchema,
} from '../../validation/events'

export type ListPath = '/' | '/archive'

const SORT_LABELS: Record<EventSort, string> = {
  soonest: 'Soonest first',
  latest: 'Latest first',
  newest: 'Newly added',
  price_asc: 'Price, low to high',
  price_desc: 'Price, high to low',
  rating_desc: 'Best rated',
}

const activeLink = 'underline decoration-2 underline-offset-[0.35em]'

/** A filter as a word. A change keeps the other filters and starts again from page 1. */
function FilterLink({
  from,
  patch,
  active,
  children,
}: {
  from: ListPath
  patch: Partial<EventsSearch>
  active: boolean
  children: ReactNode
}) {
  return (
    <Link
      from={from}
      to="."
      search={(prev: EventsSearch) => ({ ...prev, ...patch, page: undefined })}
      // The router marks a link current only when its target is exactly this URL. An active
      // tag links to "tag off", so it is marked here instead.
      activeOptions={{ exact: true }}
      aria-current={active ? 'true' : undefined}
      className={`text-small text-ink no-underline hover:underline hover:underline-offset-4 ${
        active ? activeLink : ''
      }`}
    >
      {children}
    </Link>
  )
}

function FilterRow({ label, children }: { label: string; children: ReactNode }) {
  return (
    <div className="flex flex-col gap-1.5 sm:flex-row sm:items-baseline sm:gap-4">
      <span className="eyebrow w-24 shrink-0">{label}</span>
      <div className="flex flex-wrap gap-x-5 gap-y-1.5">{children}</div>
    </div>
  )
}

interface EventFiltersProps {
  from: ListPath
  search: EventsSearch
  cities: string[]
  tags: string[]
  organizerName: string | undefined
  personName: string | undefined
}

export function EventFilters({
  from,
  search,
  cities,
  tags,
  organizerName,
  personName,
}: EventFiltersProps) {
  // A value from the URL stays visible even when it is not in the lists from the API.
  const shownTags = search.tag && !tags.includes(search.tag) ? [search.tag, ...tags] : tags
  const shownCities =
    search.city && !cities.includes(search.city) ? [search.city, ...cities] : cities

  return (
    <div className="grid gap-4 border-y border-rule py-4">
      <SearchForm key={search.search ?? ''} from={from} value={search.search} />

      <FilterRow label="Category">
        <FilterLink from={from} patch={{ category: undefined }} active={!search.category}>
          All
        </FilterLink>
        {CATEGORIES.map((category) => (
          <FilterLink
            key={category}
            from={from}
            patch={{ category }}
            active={search.category === category}
          >
            {CATEGORY_LABELS[category]}
          </FilterLink>
        ))}
      </FilterRow>

      {shownCities.length > 0 && (
        <FilterRow label="City">
          <FilterLink from={from} patch={{ city: undefined }} active={!search.city}>
            Everywhere
          </FilterLink>
          {shownCities.map((city) => (
            <FilterLink key={city} from={from} patch={{ city }} active={search.city === city}>
              {city}
            </FilterLink>
          ))}
        </FilterRow>
      )}

      {shownTags.length > 0 && (
        <FilterRow label="Tags">
          {shownTags.map((tag) => {
            const active = search.tag === tag
            return (
              <FilterLink
                key={tag}
                from={from}
                patch={{ tag: active ? undefined : tag }}
                active={active}
              >
                <span className="text-muted">#</span>
                {tag}
              </FilterLink>
            )
          })}
        </FilterRow>
      )}

      <MoreFilters from={from} search={search} />

      {(search.organizer || search.person) && (
        <FilterRow label="Showing">
          {search.organizer && (
            <FilterLink from={from} patch={{ organizer: undefined }} active>
              Organizer: {organizerName ?? 'selected organizer'}{' '}
              <span aria-hidden="true">×</span>
              <span className="sr-only">, remove</span>
            </FilterLink>
          )}
          {search.person && (
            <FilterLink from={from} patch={{ person: undefined }} active>
              With {personName ?? search.person} <span aria-hidden="true">×</span>
              <span className="sr-only">, remove</span>
            </FilterLink>
          )}
        </FilterRow>
      )}
    </div>
  )
}

function SearchForm({ from, value }: { from: ListPath; value: string | undefined }) {
  const navigate = useNavigate({ from })
  const form = useForm<EventSearchFormValues>({
    resolver: zodResolver(eventSearchFormSchema),
    defaultValues: { search: value ?? '' },
  })
  const error = form.formState.errors.search?.message

  return (
    <form
      role="search"
      noValidate
      className="flex flex-wrap items-end gap-3"
      onSubmit={form.handleSubmit(async (values) => {
        await navigate({
          search: (prev: EventsSearch) => ({
            ...prev,
            search: values.search || undefined,
            page: undefined,
          }),
        })
      })}
    >
      <div className="flex min-w-0 flex-1 flex-col gap-1">
        <label htmlFor="event-search" className="eyebrow">
          Search
        </label>
        <input
          id="event-search"
          type="search"
          placeholder="Title, venue, person or tag"
          aria-invalid={error ? true : undefined}
          aria-describedby={error ? 'event-search-error' : undefined}
          className="w-full border-0 border-b border-ink bg-transparent py-1.5 text-body text-ink placeholder:text-muted"
          {...form.register('search')}
        />
        {error && (
          <p id="event-search-error" className="text-small text-danger">
            {error}
          </p>
        )}
      </div>
      <button
        type="submit"
        className="border border-ink px-4 py-1.5 text-small font-medium text-ink hover:bg-ink hover:text-paper"
      >
        Search
      </button>
    </form>
  )
}

function MoreFilters({ from, search }: { from: ListPath; search: EventsSearch }) {
  const navigate = useNavigate({ from })

  function update(patch: Partial<EventsSearch>) {
    void navigate({ search: (prev: EventsSearch) => ({ ...prev, ...patch, page: undefined }) })
  }

  const inputClass = 'border-0 border-b border-rule bg-transparent py-1 text-small text-ink'

  return (
    <div className="flex flex-wrap items-end gap-x-6 gap-y-3">
      <div className="flex flex-col gap-1">
        <label htmlFor="filter-from" className="eyebrow">
          From
        </label>
        <input
          id="filter-from"
          type="date"
          value={search.from ?? ''}
          max={search.to}
          className={inputClass}
          onChange={(e) => update({ from: e.target.value || undefined })}
        />
      </div>
      <div className="flex flex-col gap-1">
        <label htmlFor="filter-to" className="eyebrow">
          To
        </label>
        <input
          id="filter-to"
          type="date"
          value={search.to ?? ''}
          min={search.from}
          className={inputClass}
          onChange={(e) => update({ to: e.target.value || undefined })}
        />
      </div>
      <label className="flex items-center gap-2 text-small">
        <input
          type="checkbox"
          checked={search.free ?? false}
          className="size-4 accent-[var(--accent)]"
          onChange={(e) => update({ free: e.target.checked || undefined })}
        />
        Free only
      </label>
      <label className="flex items-center gap-2 text-small">
        <input
          type="checkbox"
          checked={search.seats ?? false}
          className="size-4 accent-[var(--accent)]"
          onChange={(e) => update({ seats: e.target.checked || undefined })}
        />
        Seats left
      </label>
    </div>
  )
}

export function SortSelect({ from, value }: { from: ListPath; value: EventSort }) {
  const navigate = useNavigate({ from })
  return (
    <div className="flex items-baseline gap-2">
      <label htmlFor="event-sort" className="eyebrow">
        Sort
      </label>
      <select
        id="event-sort"
        value={value}
        className="border-0 border-b border-rule bg-transparent py-1 text-small text-ink"
        onChange={(e) =>
          void navigate({
            search: (prev: EventsSearch) => ({
              ...prev,
              sort: e.target.value as EventSort,
              page: undefined,
            }),
          })
        }
      >
        {EVENT_SORTS.map((sort) => (
          <option key={sort} value={sort}>
            {SORT_LABELS[sort]}
          </option>
        ))}
      </select>
    </div>
  )
}

/** 3, 4 or 6 columns. Only wide screens have room for the choice, so it hides below that. */
export function ColumnSwitch({ from, value }: { from: ListPath; value: number }) {
  return (
    <div className="hidden items-baseline gap-3 lg:flex" role="group" aria-label="Columns">
      <span className="eyebrow">Columns</span>
      {COLUMN_CHOICES.map((cols) => (
        <Link
          key={cols}
          from={from}
          to="."
          search={(prev: EventsSearch) => ({ ...prev, cols: cols === 3 ? undefined : cols })}
          activeOptions={{ exact: true }}
          aria-label={`${cols} columns`}
          className={`font-mono text-small no-underline ${
            value === cols ? `text-ink ${activeLink}` : 'text-muted'
          }`}
        >
          {cols}
        </Link>
      ))}
    </div>
  )
}
