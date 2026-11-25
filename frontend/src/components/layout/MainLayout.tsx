import { Link, Outlet } from '@tanstack/react-router'

import { ThemeToggle } from './ThemeToggle'
import { UserMenu } from './UserMenu'

const navLink = 'text-small text-ink no-underline hover:underline hover:underline-offset-4'
const activeNav = { className: 'underline underline-offset-[0.35em]' }

export function MainLayout() {
  return (
    <div className="flex min-h-screen flex-col bg-paper text-ink">
      <header className="mx-auto w-full max-w-[1240px] px-4 pt-6 sm:px-6">
        <nav
          aria-label="Main"
          className="flex flex-wrap items-baseline justify-between gap-x-8 gap-y-3 border-b border-ink pb-4"
        >
          <Link
            to="/"
            aria-label="Seatwise"
            className="text-[1.35rem] leading-none font-extrabold tracking-[-0.04em] text-ink no-underline"
          >
            seatwise<span className="text-accent">.</span>
          </Link>
          <div className="flex flex-wrap items-baseline gap-x-6 gap-y-2">
            <Link to="/" className={navLink} activeProps={activeNav}
              activeOptions={{ exact: true, includeSearch: false }}
            >
              Events
            </Link>
            <Link
              to="/archive"
              className={navLink}
              activeProps={activeNav}
              activeOptions={{ includeSearch: false }}
            >
              Archive
            </Link>
            <UserMenu />
            <ThemeToggle />
          </div>
        </nav>
      </header>
      <main className="mx-auto w-full max-w-[1240px] flex-1 px-4 py-8 sm:px-6">
        <Outlet />
      </main>
    </div>
  )
}
