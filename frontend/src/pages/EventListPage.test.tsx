import { screen, waitFor, within } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { http, HttpResponse } from 'msw'
import { describe, expect, it } from 'vitest'

import type { EventItem } from '../api/types'
import { renderWithProviders } from '../test/renderWithProviders'
import { apiUrl, eventsPage, makeEvent, server } from '../test/server'

/** Serves GET /events and records the query string of every call. */
function eventsRoute(items: EventItem[], calls: URLSearchParams[] = [], total = items.length) {
  return http.get(apiUrl('/events'), ({ request }) => {
    const url = new URL(request.url)
    calls.push(url.searchParams)
    return HttpResponse.json(eventsPage(items, total, Number(url.searchParams.get('page'))))
  })
}

const jazz = makeEvent()
const hamlet = makeEvent({
  id: 'e-2',
  title: 'Hamlet',
  slug: 'hamlet',
  category: 'theatre',
  city: 'Beograd',
  price: 0,
  seats_left: 0,
})

describe('home page list', () => {
  it('lists upcoming events as cards that link to the event page', async () => {
    const calls: URLSearchParams[] = []
    server.use(eventsRoute([jazz, hamlet], calls))

    await renderWithProviders('/')

    expect(await screen.findByRole('heading', { level: 1, name: 'Upcoming events' })).toBeInTheDocument()
    const card = (await screen.findByRole('heading', { name: 'Jazz Night' })).closest('a')
    expect(card).toHaveAttribute('href', '/events/jazz-night')
    expect(card && within(card).getByText('1.500 RSD')).toBeInTheDocument()
    expect(card && within(card).getByText('Studio M, Novi Sad')).toBeInTheDocument()
    const hamletCard = screen.getByRole('heading', { name: 'Hamlet' }).closest('a')
    expect(hamletCard && within(hamletCard).getByText('Free')).toBeInTheDocument()
    expect(hamletCard && within(hamletCard).getByText('Sold out')).toBeInTheDocument()
    expect(screen.getByText('2 upcoming events')).toBeInTheDocument()
    expect(calls.at(-1)?.get('when')).toBe('upcoming')
    expect(calls.at(-1)?.get('page_size')).toBe('24')
  })

  it('shows the archive with past events', async () => {
    const calls: URLSearchParams[] = []
    server.use(eventsRoute([makeEvent({ is_past: true })], calls))

    await renderWithProviders('/archive')

    expect(await screen.findByRole('heading', { level: 1, name: 'Archive' })).toBeInTheDocument()
    expect(await screen.findByText('1 past event')).toBeInTheDocument()
    expect(calls.at(-1)?.get('when')).toBe('past')
  })

  it('filters by category through the URL and starts again from page 1', async () => {
    const calls: URLSearchParams[] = []
    server.use(eventsRoute([jazz], calls))
    const { router } = await renderWithProviders('/?page=2&city=Beograd')

    await userEvent.click(await screen.findByRole('link', { name: 'Theatre' }))

    await waitFor(() =>
      expect(router.state.location.search).toEqual({ city: 'Beograd', category: 'theatre' }),
    )
    await waitFor(() => expect(calls.at(-1)?.get('category')).toBe('theatre'))
    expect(calls.at(-1)?.get('city')).toBe('Beograd')
    expect(calls.at(-1)?.get('page')).toBe('1')
    expect(screen.getByRole('link', { name: 'Theatre' })).toHaveAttribute('aria-current')
    expect(screen.getByRole('link', { name: 'All' })).not.toHaveAttribute('aria-current')
  })

  it('offers cities and popular tags from the API, and a tag toggles off', async () => {
    const calls: URLSearchParams[] = []
    server.use(
      eventsRoute([jazz], calls),
      http.get(apiUrl('/events/cities'), () => HttpResponse.json(['Beograd', 'Novi Sad'])),
      http.get(apiUrl('/events/tags'), () => HttpResponse.json(['jazz', 'open air'])),
    )
    const { router } = await renderWithProviders('/')

    await userEvent.click(await screen.findByRole('link', { name: '#open air' }))
    await waitFor(() => expect(router.state.location.search).toEqual({ tag: 'open air' }))
    await userEvent.click(screen.getByRole('link', { name: '#open air' }))

    await waitFor(() => expect(router.state.location.search).toEqual({}))
    expect(screen.getByRole('link', { name: 'Beograd' })).toBeInTheDocument()
  })

  it('searches, dates and checkboxes all go into the URL and the request', async () => {
    const calls: URLSearchParams[] = []
    server.use(eventsRoute([jazz], calls))
    const { router } = await renderWithProviders('/')

    await userEvent.type(await screen.findByLabelText('Search'), '  balasevic ')
    await userEvent.click(screen.getByRole('button', { name: 'Search' }))
    await userEvent.click(screen.getByLabelText('Free only'))
    await userEvent.click(screen.getByLabelText('Seats left'))

    await waitFor(() =>
      expect(router.state.location.search).toEqual({ search: 'balasevic', free: true, seats: true }),
    )
    await waitFor(() => expect(calls.at(-1)?.get('has_seats')).toBe('true'))
    expect(calls.at(-1)?.get('search')).toBe('balasevic')
    expect(calls.at(-1)?.get('free')).toBe('true')
  })

  it('sends a day range as the start and end of those days', async () => {
    const calls: URLSearchParams[] = []
    server.use(eventsRoute([jazz], calls))

    await renderWithProviders('/?from=2026-12-01&to=2026-12-31')

    await screen.findByRole('heading', { name: 'Jazz Night' })
    const last = calls.at(-1)
    expect(new Date(last?.get('date_from') ?? '').getDate()).toBe(1)
    expect(new Date(last?.get('date_to') ?? '').getHours()).toBe(23)
    expect(screen.getByLabelText('From')).toHaveValue('2026-12-01')
  })

  it('changes sort and columns through the URL', async () => {
    const calls: URLSearchParams[] = []
    server.use(eventsRoute([jazz], calls))
    const { router } = await renderWithProviders('/')

    await userEvent.selectOptions(await screen.findByLabelText('Sort'), 'price_asc')
    await userEvent.click(screen.getByRole('link', { name: '6 columns' }))

    await waitFor(() =>
      expect(router.state.location.search).toEqual({ sort: 'price_asc', cols: 6 }),
    )
    expect(screen.getByTestId('event-grid')).toHaveAttribute('data-columns', '6')
    expect(calls.at(-1)?.get('sort')).toBe('price_asc')
    // Columns are a view setting; the API never sees them.
    expect(calls.at(-1)?.has('cols')).toBe(false)
  })

  it('shows who a person filter is for, and removes it', async () => {
    const withAna = makeEvent({ participants: [{ name: 'Ana Anić', role: null, key: 'ana-anic' }] })
    server.use(eventsRoute([withAna]))
    const { router } = await renderWithProviders('/?person=ana-anic')

    const chip = await screen.findByRole('link', { name: /With Ana Anić/ })
    await userEvent.click(chip)

    await waitFor(() => expect(router.state.location.search).toEqual({}))
  })

  it('pages through results', async () => {
    const calls: URLSearchParams[] = []
    server.use(eventsRoute([jazz], calls, 60))
    const { router } = await renderWithProviders('/')

    expect(await screen.findByText('Page 1 of 3')).toBeInTheDocument()
    await userEvent.click(screen.getByRole('link', { name: 'Next' }))

    expect(await screen.findByText('Page 2 of 3')).toBeInTheDocument()
    expect(router.state.location.search).toEqual({ page: 2 })
    expect(calls.at(-1)?.get('page')).toBe('2')
  })

  it('says when nothing matches and offers to clear the filters', async () => {
    const { router } = await renderWithProviders('/?category=sport&cols=4')

    expect(await screen.findByText('No upcoming events match these filters.')).toBeInTheDocument()
    await userEvent.click(screen.getByRole('link', { name: 'Clear filters' }))

    await waitFor(() => expect(router.state.location.search).toEqual({ cols: 4 }))
  })
})
