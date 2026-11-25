import { screen } from '@testing-library/react'
import { http, HttpResponse } from 'msw'
import { describe, expect, it } from 'vitest'

import type { EventItem } from '../api/types'
import { renderWithProviders } from '../test/renderWithProviders'
import { apiUrl, errorResponse, makeEvent, server } from '../test/server'

function serve(event: EventItem) {
  server.use(
    http.get(apiUrl(`/events/by-slug/${event.slug}`), () => HttpResponse.json(event)),
  )
}

describe('event page', () => {
  it('shows the details, with links back into the filtered list', async () => {
    serve(
      makeEvent({
        address: 'Ignjata Pavlasa 3',
        tags: ['jazz'],
        participants: [{ name: 'Ana Anić', role: 'Director', key: 'ana-anic' }],
      }),
    )

    await renderWithProviders('/events/jazz-night')

    expect(await screen.findByRole('heading', { level: 1, name: 'Jazz Night' })).toBeInTheDocument()
    expect(screen.getByText('Sat 12 Dec 2026, 20:00 to 23:00')).toBeInTheDocument()
    expect(screen.getByText('1.500 RSD')).toBeInTheDocument()
    expect(screen.getByText('38 of 200 left')).toBeInTheDocument()
    expect(screen.getByRole('link', { name: 'Ana Anić' })).toHaveAttribute(
      'href',
      '/?person=ana-anic',
    )
    expect(screen.getByText('Director')).toBeInTheDocument()
    expect(screen.getByRole('link', { name: 'Kulturni centar' })).toHaveAttribute(
      'href',
      '/?organizer=u-org',
    )
    expect(screen.getByRole('link', { name: 'Novi Sad' })).toHaveAttribute('href', '/?city=Novi+Sad')
    expect(screen.getByRole('link', { name: '#jazz' })).toHaveAttribute('href', '/?tag=jazz')
  })

  it('renders the description markup, cleaned again in the browser', async () => {
    serve(
      makeEvent({
        description:
          '<h2>Program</h2><p onclick="steal()">Evening<img src=x onerror="steal()"><script>steal()</script></p>',
      }),
    )

    const { container } = await renderWithProviders('/events/jazz-night')

    expect(await screen.findByRole('heading', { level: 2, name: 'Program' })).toBeInTheDocument()
    const description = container.querySelector('.event-description')
    expect(description?.innerHTML).toBe('<h2>Program</h2><p>Evening</p>')
  })

  it('links a past event into the archive', async () => {
    serve(makeEvent({ is_past: true, tags: ['jazz'] }))

    await renderWithProviders('/events/jazz-night')

    expect(await screen.findByText('This event has ended.')).toBeInTheDocument()
    expect(screen.getByRole('link', { name: '#jazz' })).toHaveAttribute('href', '/archive?tag=jazz')
  })

  it('says when an event was cancelled', async () => {
    serve(makeEvent({ status: 'cancelled' }))

    await renderWithProviders('/events/jazz-night')

    expect(await screen.findByRole('status')).toHaveTextContent('This event was cancelled.')
  })

  it('shows a not found page for an unknown slug', async () => {
    server.use(
      http.get(apiUrl('/events/by-slug/nothing'), () => errorResponse(404, 'EVENT_NOT_FOUND')),
    )

    await renderWithProviders('/events/nothing')

    expect(await screen.findByRole('heading', { name: 'Event not found' })).toBeInTheDocument()
    expect(screen.getByRole('link', { name: 'Back to upcoming events' })).toHaveAttribute('href', '/')
  })
})
