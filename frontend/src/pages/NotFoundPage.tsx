import { Link } from '@tanstack/react-router'

export function NotFoundPage() {
  return (
    <section>
      <h1 className="display text-h2">Page not found</h1>
      <p className="mt-2 text-muted">The page you are looking for does not exist.</p>
      <Link to="/" className="mt-4 inline-block font-medium text-accent underline">
        Back to upcoming events
      </Link>
    </section>
  )
}
