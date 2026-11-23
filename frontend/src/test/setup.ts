import '@testing-library/jest-dom/vitest'
import { cleanup } from '@testing-library/react'
import { afterAll, afterEach, beforeAll, vi } from 'vitest'

import { resetSessionForTests } from '../auth/session'
import { resetAuthStore } from '../store/auth'
import { server } from './server'

// jsdom does not implement scrolling; the router calls it on navigation.
window.scrollTo = vi.fn() as unknown as typeof window.scrollTo

// A request with no handler fails the test, so no test talks to a real server.
beforeAll(() => server.listen({ onUnhandledFrame: 'error' }))

afterEach(() => {
  cleanup()
  server.resetHandlers()
  resetAuthStore()
  resetSessionForTests()
})

afterAll(() => server.close())
