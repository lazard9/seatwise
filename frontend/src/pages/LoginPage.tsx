import { zodResolver } from '@hookform/resolvers/zod'
import { useMutation } from '@tanstack/react-query'
import { getRouteApi, Link, useNavigate } from '@tanstack/react-router'
import { useForm } from 'react-hook-form'

import { login } from '../api/auth'
import { Button } from '../components/ui/Button'
import { FormError } from '../components/ui/FormError'
import { TextField } from '../components/ui/TextField'
import { useAuthStore } from '../store/auth'
import { apiErrorMessage } from '../utils/apiErrors'
import { type LoginValues, loginSchema, safeRedirect } from '../validation/auth'

const route = getRouteApi('/login')

export function LoginPage() {
  const { redirect: redirectTo } = route.useSearch()
  const navigate = useNavigate()
  const signedIn = useAuthStore((state) => state.signedIn)
  const form = useForm<LoginValues>({
    resolver: zodResolver(loginSchema),
    defaultValues: { email: '', password: '' },
  })
  const mutation = useMutation({
    mutationFn: login,
    onSuccess: async (session) => {
      signedIn(session)
      await navigate({ href: safeRedirect(redirectTo) })
    },
  })
  const { errors } = form.formState

  return (
    <section className="mx-auto max-w-sm">
      <h1 className="display text-h2">Sign in</h1>
      <form
        noValidate
        className="mt-6 flex flex-col gap-4"
        onSubmit={form.handleSubmit((values) => mutation.mutate(values))}
      >
        <FormError message={mutation.isError ? apiErrorMessage(mutation.error) : undefined} />
        <TextField
          label="Email"
          type="email"
          autoComplete="email"
          error={errors.email?.message}
          {...form.register('email')}
        />
        <TextField
          label="Password"
          type="password"
          autoComplete="current-password"
          error={errors.password?.message}
          {...form.register('password')}
        />
        <Button type="submit" disabled={mutation.isPending}>
          {mutation.isPending ? 'Signing in…' : 'Sign in'}
        </Button>
      </form>
      <p className="mt-4 text-sm text-muted">
        No account yet?{' '}
        <Link to="/register" search={{ redirect: redirectTo }} className="font-medium text-accent underline">
          Create one
        </Link>
      </p>
    </section>
  )
}
