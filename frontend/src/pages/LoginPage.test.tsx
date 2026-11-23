import { screen, waitFor } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { http, HttpResponse } from 'msw'
import { describe, expect, it } from 'vitest'

import { useAuthStore } from '../store/auth'
import { renderWithProviders } from '../test/renderWithProviders'
import {
  apiUrl,
  errorResponse,
  makeUser,
  server,
  signedInAs,
  tokenResponse,
} from '../test/server'

describe('login page', () => {
  it('signs in and returns to the home page', async () => {
    const user = makeUser({ display_name: 'Ana' })
    let body: unknown
    server.use(
      http.post(apiUrl('/auth/login'), async ({ request }) => {
        body = await request.json()
        return HttpResponse.json(tokenResponse(user))
      }),
    )
    const { router } = await renderWithProviders('/login')

    await userEvent.type(await screen.findByLabelText('Email'), 'ana@example.com')
    await userEvent.type(screen.getByLabelText('Password'), 'long-enough-password')
    await userEvent.click(screen.getByRole('button', { name: 'Sign in' }))

    await waitFor(() => expect(router.state.location.pathname).toBe('/'))
    expect(body).toEqual({ email: 'ana@example.com', password: 'long-enough-password' })
    expect(useAuthStore.getState().user).toEqual(user)
    expect(await screen.findByText('Ana')).toBeInTheDocument()
  })

  it('shows the error for wrong credentials and stays on the page', async () => {
    server.use(
      http.post(apiUrl('/auth/login'), () => errorResponse(401, 'INVALID_CREDENTIALS')),
    )
    const { router } = await renderWithProviders('/login')

    await userEvent.type(await screen.findByLabelText('Email'), 'ana@example.com')
    await userEvent.type(screen.getByLabelText('Password'), 'wrong-password')
    await userEvent.click(screen.getByRole('button', { name: 'Sign in' }))

    expect(await screen.findByRole('alert')).toHaveTextContent('Email or password is incorrect.')
    expect(router.state.location.pathname).toBe('/login')
    expect(useAuthStore.getState().status).toBe('guest')
  })

  it('validates before sending anything', async () => {
    let requests = 0
    server.use(
      http.post(apiUrl('/auth/login'), () => {
        requests += 1
        return errorResponse(401, 'INVALID_CREDENTIALS')
      }),
    )
    await renderWithProviders('/login')

    await userEvent.click(await screen.findByRole('button', { name: 'Sign in' }))

    expect(await screen.findByText('Enter your email address.')).toBeInTheDocument()
    expect(screen.getByText('Enter your password.')).toBeInTheDocument()
    expect(screen.getByLabelText('Email')).toHaveAttribute('aria-invalid', 'true')
    expect(requests).toBe(0)
  })

  it('sends a signed-in user away from the page', async () => {
    signedInAs('attendee')

    const { router } = await renderWithProviders('/login')

    expect(router.state.location.pathname).toBe('/')
  })

  it('ignores a redirect to another site', async () => {
    server.use(
      http.post(apiUrl('/auth/login'), () => HttpResponse.json(tokenResponse(makeUser()))),
    )
    const { router } = await renderWithProviders('/login?redirect=//evil.example')

    await userEvent.type(await screen.findByLabelText('Email'), 'ana@example.com')
    await userEvent.type(screen.getByLabelText('Password'), 'long-enough-password')
    await userEvent.click(screen.getByRole('button', { name: 'Sign in' }))

    await waitFor(() => expect(router.state.location.href).toBe('/'))
  })
})
