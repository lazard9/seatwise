import { type ErrorComponentProps, Link } from '@tanstack/react-router'

import { ForbiddenError } from '../auth/guards'

/** Shown in place of a page whose guard or loader failed. The layout stays. */
export function RouteErrorPage({ error }: ErrorComponentProps) {
  const forbidden = error instanceof ForbiddenError
  return (
    <section>
      <h1 className="text-2xl font-bold">{forbidden ? 'No access' : 'Something went wrong'}</h1>
      <p className="mt-2 text-slate-600">
        {forbidden
          ? 'Your account does not have access to this page.'
          : 'The page could not be loaded. Please try again.'}
      </p>
      <Link to="/" className="mt-4 inline-block font-medium text-indigo-700 underline">
        Back to upcoming events
      </Link>
    </section>
  )
}
