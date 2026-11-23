import { screen, waitFor, within } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { http, HttpResponse } from 'msw'
import { describe, expect, it } from 'vitest'

import type { Page, User } from '../api/types'
import { renderWithProviders } from '../test/renderWithProviders'
import {
  apiUrl,
  errorResponse,
  makeUser,
  server,
  signedInAs,
  tokenResponse,
} from '../test/server'

const ADMIN_ID = 'u-admin'

function usersPage(items: User[], total = items.length, page = 1): Page<User> {
  return { items, total, page, page_size: 20 }
}

/** Serves GET /users and records the query string of every call. */
function usersRoute(respond: (url: URL) => Page<User>, calls: URLSearchParams[] = []) {
  return http.get(apiUrl('/users'), ({ request }) => {
    const url = new URL(request.url)
    calls.push(url.searchParams)
    return HttpResponse.json(respond(url))
  })
}

const marko = makeUser({ id: 'u-marko', email: 'marko@example.com', display_name: 'Marko' })

function signInAsAdmin(): User {
  return signedInAs('admin', { id: ADMIN_ID, email: 'admin@example.com', display_name: 'Admin' })
}

describe('admin users page: access', () => {
  it('sends a guest to sign in, then back to the page', async () => {
    const admin = makeUser({ id: ADMIN_ID, role: 'admin' })
    server.use(
      http.post(apiUrl('/auth/login'), () => HttpResponse.json(tokenResponse(admin))),
      usersRoute(() => usersPage([admin])),
    )

    const { router } = await renderWithProviders('/admin/users?role=admin')

    expect(router.state.location.pathname).toBe('/login')
    await userEvent.type(await screen.findByLabelText('Email'), 'admin@example.com')
    await userEvent.type(screen.getByLabelText('Password'), 'long-enough-password')
    await userEvent.click(screen.getByRole('button', { name: 'Sign in' }))

    expect(await screen.findByRole('heading', { name: 'Users' })).toBeInTheDocument()
    expect(router.state.location.pathname).toBe('/admin/users')
    expect(router.state.location.search).toEqual({ role: 'admin' })
  })

  it.each(['organizer', 'attendee'] as const)('shows no access to an %s', async (role) => {
    signedInAs(role)

    await renderWithProviders('/admin/users')

    expect(await screen.findByRole('heading', { name: 'No access' })).toBeInTheDocument()
    expect(screen.getByRole('button', { name: 'Sign out' })).toBeInTheDocument()
  })

  it.each([
    ['admin', true],
    ['organizer', false],
    ['attendee', false],
  ] as const)('the Users link in the header for %s: %s', async (role, shown) => {
    signedInAs(role)

    await renderWithProviders('/')

    await screen.findByRole('button', { name: 'Sign out' })
    expect(screen.queryByRole('link', { name: 'Users' }) !== null).toBe(shown)
  })
})

describe('admin users page: list', () => {
  it('lists users, and the admin cannot change their own role', async () => {
    const admin = signInAsAdmin()
    server.use(usersRoute(() => usersPage([marko, admin])))

    await renderWithProviders('/admin/users')

    const markoRow = (await screen.findByText('marko@example.com')).closest('tr')
    const adminRow = screen.getByText('admin@example.com').closest('tr')
    expect(markoRow && within(markoRow).getByRole('combobox')).toBeEnabled()
    expect(adminRow && within(adminRow).getByRole('combobox')).toBeDisabled()
    expect(adminRow && within(adminRow).getByText('(you)')).toBeInTheDocument()
    expect(screen.getByText('2 users')).toBeInTheDocument()
  })

  it('changes a role and reloads the list', async () => {
    signInAsAdmin()
    let role: User['role'] = 'attendee'
    let patched: unknown
    server.use(
      usersRoute(() => usersPage([{ ...marko, role }])),
      http.patch(apiUrl('/users/u-marko/role'), async ({ request }) => {
        patched = await request.json()
        role = 'organizer'
        return HttpResponse.json({ ...marko, role })
      }),
    )
    await renderWithProviders('/admin/users')

    await userEvent.selectOptions(
      await screen.findByRole('combobox', { name: 'Role of marko@example.com' }),
      'organizer',
    )

    expect(patched).toEqual({ role: 'organizer' })
    await waitFor(() =>
      expect(screen.getByRole('combobox', { name: 'Role of marko@example.com' })).toHaveValue(
        'organizer',
      ),
    )
  })

  it('shows the reason when a change is refused', async () => {
    signInAsAdmin()
    server.use(
      usersRoute(() => usersPage([marko])),
      http.patch(apiUrl('/users/u-marko/role'), () => errorResponse(404, 'USER_NOT_FOUND')),
    )
    await renderWithProviders('/admin/users')

    await userEvent.selectOptions(
      await screen.findByRole('combobox', { name: 'Role of marko@example.com' }),
      'admin',
    )

    expect(await screen.findByRole('alert')).toHaveTextContent('This user no longer exists.')
  })

  it('puts the filter in the URL and starts from page 1', async () => {
    signInAsAdmin()
    const calls: URLSearchParams[] = []
    server.use(usersRoute(() => usersPage([marko]), calls))
    const { router } = await renderWithProviders('/admin/users?page=3')

    await userEvent.type(await screen.findByLabelText('Search by name or email'), '  mark ')
    await userEvent.selectOptions(screen.getByLabelText('Role'), 'attendee')
    await userEvent.click(screen.getByRole('button', { name: 'Apply' }))

    await waitFor(() =>
      expect(router.state.location.search).toEqual({ search: 'mark', role: 'attendee' }),
    )
    const last = calls.at(-1)
    expect(last?.get('search')).toBe('mark')
    expect(last?.get('role')).toBe('attendee')
    expect(last?.get('page')).toBe('1')
  })

  it('reads the filter from the URL on load', async () => {
    signInAsAdmin()
    const calls: URLSearchParams[] = []
    server.use(usersRoute(() => usersPage([marko]), calls))

    await renderWithProviders('/admin/users?search=mark&role=organizer&page=2')

    expect(await screen.findByLabelText('Search by name or email')).toHaveValue('mark')
    expect(screen.getByLabelText('Role')).toHaveValue('organizer')
    await waitFor(() => expect(calls.at(-1)?.get('page')).toBe('2'))
  })

  it('ignores invalid values in the URL', async () => {
    signInAsAdmin()
    const calls: URLSearchParams[] = []
    server.use(usersRoute(() => usersPage([marko]), calls))

    await renderWithProviders('/admin/users?page=-4&role=boss')

    await screen.findByText('marko@example.com')
    expect(calls.at(-1)?.get('page')).toBe('1')
    expect(calls.at(-1)?.has('role')).toBe(false)
  })

  it('moves between pages', async () => {
    signInAsAdmin()
    const calls: URLSearchParams[] = []
    server.use(
      usersRoute((url) => usersPage([marko], 45, Number(url.searchParams.get('page'))), calls),
    )
    const { router } = await renderWithProviders('/admin/users')

    expect(await screen.findByText('Page 1 of 3')).toBeInTheDocument()
    expect(screen.queryByRole('link', { name: 'Previous' })).not.toBeInTheDocument()
    await userEvent.click(screen.getByRole('link', { name: 'Next' }))

    expect(await screen.findByText('Page 2 of 3')).toBeInTheDocument()
    expect(router.state.location.search).toEqual({ page: 2 })
    expect(calls.at(-1)?.get('page')).toBe('2')
  })
})
