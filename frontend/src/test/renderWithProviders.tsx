import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { createMemoryHistory, RouterProvider } from '@tanstack/react-router'
import { render } from '@testing-library/react'

import { createAppRouter } from '../router'

/**
 * Renders the whole app at `path`, with a fresh QueryClient (retries off)
 * and in-memory history, so each test starts from a clean state.
 */
export async function renderWithProviders(path = '/') {
  const queryClient = new QueryClient({
    defaultOptions: {
      queries: { retry: false, gcTime: Infinity },
      mutations: { retry: false },
    },
  })
  const history = createMemoryHistory({ initialEntries: [path] })
  const router = createAppRouter(queryClient, history)
  await router.load()

  const result = render(
    <QueryClientProvider client={queryClient}>
      <RouterProvider router={router} />
    </QueryClientProvider>,
  )
  return { ...result, router, queryClient }
}
