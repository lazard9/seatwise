import { screen } from '@testing-library/react'
import { describe, expect, it } from 'vitest'

import { renderWithProviders } from '../test/renderWithProviders'

describe('app shell', () => {
  it('renders the home page at /', async () => {
    await renderWithProviders('/')

    expect(
      await screen.findByRole('heading', { level: 1, name: 'Upcoming events' }),
    ).toBeInTheDocument()
    expect(screen.getByRole('link', { name: 'Seatwise' })).toHaveAttribute('href', '/')
  })

  it('renders the not found page for an unknown path', async () => {
    await renderWithProviders('/no-such-page')

    expect(await screen.findByRole('heading', { name: 'Page not found' })).toBeInTheDocument()
    expect(screen.getByRole('link', { name: 'Back to upcoming events' })).toHaveAttribute(
      'href',
      '/',
    )
  })
})
