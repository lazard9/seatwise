import { screen, waitFor } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { http, HttpResponse } from 'msw'
import { describe, expect, it } from 'vitest'

import { useAuthStore } from '../store/auth'
import { renderWithProviders } from '../test/renderWithProviders'
import { apiUrl, errorResponse, makeUser, server, tokenResponse } from '../test/server'

async function fillForm(email = 'ana@example.com', name = 'Ana', password = 'long-enough-password') {
  await userEvent.type(await screen.findByLabelText('Email'), email)
  await userEvent.type(screen.getByLabelText('Display name'), name)
  await userEvent.type(screen.getByLabelText('Password'), password)
  await userEvent.click(screen.getByRole('button', { name: 'Create account' }))
}

describe('register page', () => {
  it('creates the account, signs in and goes home', async () => {
    const user = makeUser()
    let registered: unknown
    server.use(
      http.post(apiUrl('/auth/register'), async ({ request }) => {
        registered = await request.json()
        return HttpResponse.json(user, { status: 201 })
      }),
      http.post(apiUrl('/auth/login'), () => HttpResponse.json(tokenResponse(user))),
    )
    const { router } = await renderWithProviders('/register')

    await fillForm('  ana@example.com ', '  Ana  ')

    await waitFor(() => expect(router.state.location.pathname).toBe('/'))
    expect(registered).toEqual({
      email: 'ana@example.com',
      display_name: 'Ana',
      password: 'long-enough-password',
    })
    expect(useAuthStore.getState().status).toBe('signedIn')
  })

  it('shows a taken email next to the email field', async () => {
    server.use(http.post(apiUrl('/auth/register'), () => errorResponse(409, 'EMAIL_TAKEN')))
    await renderWithProviders('/register')

    await fillForm()

    expect(
      await screen.findByText('An account with this email already exists.'),
    ).toBeInTheDocument()
    expect(screen.getByLabelText('Email')).toHaveAttribute('aria-invalid', 'true')
    expect(screen.queryByRole('alert')).not.toBeInTheDocument()
  })

  it('applies the same field rules as the backend', async () => {
    let requests = 0
    server.use(
      http.post(apiUrl('/auth/register'), () => {
        requests += 1
        return HttpResponse.json(makeUser(), { status: 201 })
      }),
    )
    await renderWithProviders('/register')

    await fillForm('not-an-email', 'A', 'short')

    expect(await screen.findByText('Enter a valid email address.')).toBeInTheDocument()
    expect(screen.getByText('Use at least 2 characters.')).toBeInTheDocument()
    expect(screen.getByText('Use at least 8 characters.')).toBeInTheDocument()
    expect(requests).toBe(0)
  })
})
