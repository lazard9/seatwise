import { isAxiosError } from 'axios'
import { http, HttpResponse } from 'msw'
import { describe, expect, it } from 'vitest'

import { useAuthStore } from '../store/auth'
import { apiUrl, errorResponse, makeUser, server, tokenResponse } from '../test/server'
import { api, refreshSession } from './client'

const user = makeUser()

function signIn(token: string): void {
  useAuthStore.getState().signedIn(tokenResponse(user, token))
}

/** /data answers 200 only for `Bearer fresh`, like an API after the old token expired. */
function protectedDataRoute(seen: string[] = []) {
  return http.get(apiUrl('/data'), ({ request }) => {
    const auth = request.headers.get('Authorization') ?? ''
    seen.push(auth)
    return auth === 'Bearer fresh'
      ? HttpResponse.json({ ok: true })
      : errorResponse(401, 'TOKEN_EXPIRED')
  })
}

function refreshRoute(counter: { calls: number }, succeed = true) {
  return http.post(apiUrl('/auth/refresh'), () => {
    counter.calls += 1
    return succeed
      ? HttpResponse.json(tokenResponse(user, 'fresh'))
      : errorResponse(401, 'INVALID_REFRESH_TOKEN')
  })
}

describe('api client', () => {
  it('sends the access token from the store', async () => {
    const seen: string[] = []
    server.use(protectedDataRoute(seen))
    signIn('fresh')

    await api.get('/data')

    expect(seen).toEqual(['Bearer fresh'])
  })

  it('refreshes once on 401 and retries with the new token', async () => {
    const seen: string[] = []
    const refresh = { calls: 0 }
    server.use(protectedDataRoute(seen), refreshRoute(refresh))
    signIn('expired')

    const response = await api.get('/data')

    expect(response.data).toEqual({ ok: true })
    expect(refresh.calls).toBe(1)
    expect(seen).toEqual(['Bearer expired', 'Bearer fresh'])
    expect(useAuthStore.getState().accessToken).toBe('fresh')
  })

  it('shares one refresh between requests that fail together', async () => {
    const refresh = { calls: 0 }
    server.use(protectedDataRoute(), refreshRoute(refresh))
    signIn('expired')

    const responses = await Promise.all([api.get('/data'), api.get('/data'), api.get('/data')])

    expect(responses.map((r) => r.status)).toEqual([200, 200, 200])
    expect(refresh.calls).toBe(1)
  })

  it('signs out and passes the 401 on when the refresh fails', async () => {
    const refresh = { calls: 0 }
    server.use(protectedDataRoute(), refreshRoute(refresh, false))
    signIn('expired')

    const error = await api.get('/data').catch((e: unknown) => e)

    expect(isAxiosError(error) && error.response?.status).toBe(401)
    expect(useAuthStore.getState().status).toBe('guest')
    expect(useAuthStore.getState().accessToken).toBeNull()
  })

  it('retries only once: a second 401 goes to the caller', async () => {
    const refresh = { calls: 0 }
    server.use(
      http.get(apiUrl('/data'), () => errorResponse(401, 'INVALID_TOKEN')),
      refreshRoute(refresh),
    )
    signIn('expired')

    const error = await api.get('/data').catch((e: unknown) => e)

    expect(isAxiosError(error) && error.response?.status).toBe(401)
    expect(refresh.calls).toBe(1)
  })

  it('does not refresh when an auth route answers 401', async () => {
    const refresh = { calls: 0 }
    server.use(
      http.post(apiUrl('/auth/login'), () => errorResponse(401, 'INVALID_CREDENTIALS')),
      refreshRoute(refresh),
    )

    await api
      .post('/auth/login', {}, { skipAuthRefresh: true })
      .catch((e: unknown) => e)

    expect(refresh.calls).toBe(0)
  })

  it('does not refresh on other errors', async () => {
    const refresh = { calls: 0 }
    server.use(
      http.get(apiUrl('/data'), () => errorResponse(403, 'FORBIDDEN_ROLE')),
      refreshRoute(refresh),
    )
    signIn('fresh')

    await api.get('/data').catch((e: unknown) => e)

    expect(refresh.calls).toBe(0)
  })

  it('refreshSession reports the outcome and updates the store', async () => {
    const refresh = { calls: 0 }
    server.use(refreshRoute(refresh))

    expect(await refreshSession()).toBe(true)
    expect(useAuthStore.getState()).toMatchObject({ status: 'signedIn', user })
  })
})
