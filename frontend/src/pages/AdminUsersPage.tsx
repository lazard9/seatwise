import { zodResolver } from '@hookform/resolvers/zod'
import { keepPreviousData, useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { getRouteApi, Link } from '@tanstack/react-router'
import { useForm } from 'react-hook-form'

import { type Role, ROLES, type User } from '../api/types'
import { changeRole, listUsers, usersKeys } from '../api/users'
import { Button } from '../components/ui/Button'
import { FormError } from '../components/ui/FormError'
import { TextField } from '../components/ui/TextField'
import { useAuthStore } from '../store/auth'
import { apiErrorMessage } from '../utils/apiErrors'
import { type UserFilterValues, userFilterSchema } from '../validation/users'

const route = getRouteApi('/admin/users')

const PAGE_SIZE = 20

const ROLE_LABELS: Record<Role, string> = {
  admin: 'Admin',
  organizer: 'Organizer',
  attendee: 'Attendee',
}

const dateFormat = new Intl.DateTimeFormat('en-GB', { dateStyle: 'medium' })

export function AdminUsersPage() {
  const { page = 1, search, role } = route.useSearch()
  const params = { page, page_size: PAGE_SIZE, search, role }
  const query = useQuery({
    queryKey: usersKeys.list(params),
    queryFn: () => listUsers(params),
    // Keep the current page on screen while the next one loads.
    placeholderData: keepPreviousData,
  })

  const totalPages = query.data ? Math.max(1, Math.ceil(query.data.total / PAGE_SIZE)) : 1

  return (
    <section>
      <h1 className="display text-h2">Users</h1>
      <UserFilter key={`${search ?? ''}|${role ?? ''}`} search={search} role={role} />

      {query.isPending && <p className="mt-6 text-muted">Loading users…</p>}
      {query.isError && <FormError message={apiErrorMessage(query.error)} />}

      {query.data && (
        <>
          <p className="mt-6 text-sm text-muted" aria-live="polite">
            {query.data.total === 1 ? '1 user' : `${query.data.total} users`}
          </p>
          {query.data.items.length > 0 ? (
            <UsersTable users={query.data.items} />
          ) : (
            <p className="mt-4 text-muted">No users match.</p>
          )}
          <Pager page={page} totalPages={totalPages} />
        </>
      )}
    </section>
  )
}

function UserFilter({ search, role }: { search: string | undefined; role: Role | undefined }) {
  const navigate = route.useNavigate()
  const form = useForm<UserFilterValues>({
    resolver: zodResolver(userFilterSchema),
    defaultValues: { search: search ?? '', role: role ?? '' },
  })

  return (
    <form
      role="search"
      noValidate
      className="mt-6 flex flex-wrap items-end gap-4"
      onSubmit={form.handleSubmit(async (values) => {
        // A new filter starts again from the first page.
        await navigate({
          search: { search: values.search || undefined, role: values.role || undefined },
        })
      })}
    >
      <div className="min-w-60 flex-1">
        <TextField
          label="Search by name or email"
          type="search"
          error={form.formState.errors.search?.message}
          {...form.register('search')}
        />
      </div>
      <div className="flex flex-col gap-1">
        <label htmlFor="role-filter" className="text-sm font-medium text-ink">
          Role
        </label>
        <select
          id="role-filter"
          className="border border-rule bg-transparent px-3 py-2"
          {...form.register('role')}
        >
          <option value="">All roles</option>
          {ROLES.map((r) => (
            <option key={r} value={r}>
              {ROLE_LABELS[r]}
            </option>
          ))}
        </select>
      </div>
      <Button type="submit">Apply</Button>
    </form>
  )
}

function UsersTable({ users }: { users: User[] }) {
  const currentUserId = useAuthStore((state) => state.user?.id)
  const queryClient = useQueryClient()
  const mutation = useMutation({
    mutationFn: ({ userId, role }: { userId: string; role: Role }) => changeRole(userId, role),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: usersKeys.all }),
  })

  return (
    <>
      <FormError message={mutation.isError ? apiErrorMessage(mutation.error) : undefined} />
      <div className="mt-2 overflow-x-auto">
        <table className="w-full text-left text-sm">
          <thead className="border-b border-rule text-muted">
            <tr>
              <th scope="col" className="py-2 pr-4 font-medium">Name</th>
              <th scope="col" className="py-2 pr-4 font-medium">Email</th>
              <th scope="col" className="py-2 pr-4 font-medium">Role</th>
              <th scope="col" className="py-2 font-medium">Joined</th>
            </tr>
          </thead>
          <tbody>
            {users.map((user) => {
              const isSelf = user.id === currentUserId
              return (
                <tr key={user.id} className="border-b border-rule">
                  <td className="py-2 pr-4">
                    {user.display_name}
                    {isSelf && <span className="ml-2 text-muted">(you)</span>}
                  </td>
                  <td className="py-2 pr-4">{user.email}</td>
                  <td className="py-2 pr-4">
                    <select
                      aria-label={`Role of ${user.email}`}
                      value={user.role}
                      // The backend refuses it too: an admin cannot change their own role.
                      disabled={isSelf || mutation.isPending}
                      className="border border-rule bg-transparent px-2 py-1 disabled:opacity-60"
                      onChange={(event) =>
                        mutation.mutate({ userId: user.id, role: event.target.value as Role })
                      }
                    >
                      {ROLES.map((r) => (
                        <option key={r} value={r}>
                          {ROLE_LABELS[r]}
                        </option>
                      ))}
                    </select>
                  </td>
                  <td className="py-2">{dateFormat.format(new Date(user.created_at))}</td>
                </tr>
              )
            })}
          </tbody>
        </table>
      </div>
    </>
  )
}

function Pager({ page, totalPages }: { page: number; totalPages: number }) {
  if (totalPages <= 1) {
    return null
  }
  const linkClass = 'font-medium text-accent underline'
  return (
    <nav aria-label="Pages" className="mt-4 flex items-center gap-4 text-sm">
      {page > 1 && (
        <Link from="/admin/users" search={(prev) => ({ ...prev, page: page - 1 })} className={linkClass}>
          Previous
        </Link>
      )}
      <span>
        Page {page} of {totalPages}
      </span>
      {page < totalPages && (
        <Link from="/admin/users" search={(prev) => ({ ...prev, page: page + 1 })} className={linkClass}>
          Next
        </Link>
      )}
    </nav>
  )
}
