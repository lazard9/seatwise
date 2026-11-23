import { useQueryClient } from '@tanstack/react-query'
import { Link, useNavigate, useRouter } from '@tanstack/react-router'
import { useState } from 'react'

import { signOut } from '../../auth/session'
import { useAuthStore } from '../../store/auth'
import { permissions } from '../../utils/permissions'
import { Button } from '../ui/Button'

const linkClass = 'font-medium text-slate-700 hover:text-slate-900'

export function UserMenu() {
  const status = useAuthStore((state) => state.status)
  const user = useAuthStore((state) => state.user)
  const queryClient = useQueryClient()
  const router = useRouter()
  const navigate = useNavigate()
  const [signingOut, setSigningOut] = useState(false)

  if (status === 'unknown') {
    return null
  }

  if (!user) {
    return (
      <div className="flex items-center gap-4">
        <Link to="/login" className={linkClass}>
          Sign in
        </Link>
        <Link to="/register" className={linkClass}>
          Sign up
        </Link>
      </div>
    )
  }

  async function handleSignOut() {
    setSigningOut(true)
    await signOut()
    // Nothing fetched for this user may be shown to the next one.
    queryClient.clear()
    await navigate({ to: '/' })
    await router.invalidate()
    setSigningOut(false)
  }

  return (
    <div className="flex items-center gap-4">
      {permissions.manageUsers(user) && (
        <Link to="/admin/users" className={linkClass}>
          Users
        </Link>
      )}
      <span className="text-sm text-slate-600">
        Signed in as <span className="font-medium text-slate-900">{user.display_name}</span>
      </span>
      <Button variant="secondary" onClick={handleSignOut} disabled={signingOut}>
        Sign out
      </Button>
    </div>
  )
}
