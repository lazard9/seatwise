import { http, HttpResponse } from 'msw'
import { describe, expect, it } from 'vitest'

import { useAuthStore } from '../store/auth'
import { apiUrl, errorResponse, makeUser, server, signedInAs, tokenResponse } from '../test/server'
import { ensureSession, signOut } from './session'

describe('session', () => {
  it('starts as unknown, before the first check', () => {
    expect(useAuthStore.getState().status).toBe('unknown')
  })

  it('restores the user from the refresh cookie on start', async () => {
    const user = signedInAs('organizer')

    await ensureSession()

    expect(useAuthStore.getState()).toMatchObject({ status: 'signedIn', user })
  })

  it('becomes a guest when there is no session', async () => {
    await ensureSession()

    expect(useAuthStore.getState().status).toBe('guest')
  })

  it('becomes a guest when the server cannot be reached', async () => {
    server.use(http.post(apiUrl('/auth/refresh'), () => HttpResponse.error()))

    await ensureSession()

    expect(useAuthStore.getState().status).toBe('guest')
  })

  it('checks only once per page load', async () => {
    let calls = 0
    server.use(
      http.post(apiUrl('/auth/refresh'), () => {
        calls += 1
        return errorResponse(401, 'NOT_AUTHENTICATED')
      }),
    )

    await Promise.all([ensureSession(), ensureSession()])
    await ensureSession()

    expect(calls).toBe(1)
  })

  it('signs out locally even when the server fails', async () => {
    useAuthStore.getState().signedIn(tokenResponse(makeUser()))
    server.use(http.post(apiUrl('/auth/logout'), () => HttpResponse.error()))

    await signOut()

    expect(useAuthStore.getState()).toMatchObject({ status: 'guest', user: null })
  })
})
