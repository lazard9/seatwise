import { screen, waitFor } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { http, HttpResponse } from 'msw'
import { describe, expect, it } from 'vitest'

import { useAuthStore } from '../../store/auth'
import { renderWithProviders } from '../../test/renderWithProviders'
import { apiUrl, server, signedInAs } from '../../test/server'

describe('user menu', () => {
  it('offers sign in and sign up to guests', async () => {
    await renderWithProviders('/')

    expect(await screen.findByRole('link', { name: 'Sign in' })).toHaveAttribute('href', '/login')
    expect(screen.getByRole('link', { name: 'Sign up' })).toHaveAttribute('href', '/register')
  })

  it('shows who is signed in after the session check on start', async () => {
    signedInAs('attendee', { display_name: 'Marko' })

    await renderWithProviders('/')

    expect(await screen.findByText('Marko')).toBeInTheDocument()
    expect(screen.queryByRole('link', { name: 'Sign in' })).not.toBeInTheDocument()
  })

  it('signs out on the server and here', async () => {
    signedInAs('attendee', { display_name: 'Marko' })
    let loggedOut = false
    server.use(
      http.post(apiUrl('/auth/logout'), () => {
        loggedOut = true
        return new HttpResponse(null, { status: 204 })
      }),
    )
    await renderWithProviders('/')

    await userEvent.click(await screen.findByRole('button', { name: 'Sign out' }))

    expect(await screen.findByRole('link', { name: 'Sign in' })).toBeInTheDocument()
    await waitFor(() => expect(loggedOut).toBe(true))
    expect(useAuthStore.getState().status).toBe('guest')
  })
})
