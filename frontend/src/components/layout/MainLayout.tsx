import { Link, Outlet } from '@tanstack/react-router'

import { UserMenu } from './UserMenu'

export function MainLayout() {
  return (
    <div className="flex min-h-screen flex-col bg-white text-slate-900">
      <header className="border-b border-slate-200">
        <nav
          aria-label="Main"
          className="mx-auto flex max-w-6xl items-center justify-between px-4 py-3"
        >
          <Link to="/" className="text-lg font-semibold tracking-tight">
            Seatwise
          </Link>
          <UserMenu />
        </nav>
      </header>
      <main className="mx-auto w-full max-w-6xl flex-1 px-4 py-8">
        <Outlet />
      </main>
    </div>
  )
}
