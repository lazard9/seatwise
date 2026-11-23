import { zodResolver } from '@hookform/resolvers/zod'
import { useMutation } from '@tanstack/react-query'
import { getRouteApi, Link, useNavigate } from '@tanstack/react-router'
import { useForm } from 'react-hook-form'

import { login, register } from '../api/auth'
import type { TokenResponse } from '../api/types'
import { Button } from '../components/ui/Button'
import { FormError } from '../components/ui/FormError'
import { TextField } from '../components/ui/TextField'
import { useAuthStore } from '../store/auth'
import { apiErrorCode, apiErrorMessage } from '../utils/apiErrors'
import {
  PASSWORD_MIN_LENGTH,
  type RegisterValues,
  registerSchema,
  safeRedirect,
} from '../validation/auth'

/** Create the account, then sign in with the same details, so one form does both. */
async function registerAndSignIn(values: RegisterValues): Promise<TokenResponse> {
  await register(values)
  return login({ email: values.email, password: values.password })
}

const route = getRouteApi('/register')

export function RegisterPage() {
  const { redirect: redirectTo } = route.useSearch()
  const navigate = useNavigate()
  const signedIn = useAuthStore((state) => state.signedIn)
  const form = useForm<RegisterValues>({
    resolver: zodResolver(registerSchema),
    defaultValues: { email: '', display_name: '', password: '' },
  })
  const mutation = useMutation({
    mutationFn: registerAndSignIn,
    onSuccess: async (session) => {
      signedIn(session)
      await navigate({ href: safeRedirect(redirectTo) })
    },
    onError: (error) => {
      if (apiErrorCode(error) === 'EMAIL_TAKEN') {
        form.setError('email', { message: apiErrorMessage(error) })
      }
    },
  })
  const { errors } = form.formState
  const formError =
    mutation.isError && apiErrorCode(mutation.error) !== 'EMAIL_TAKEN'
      ? apiErrorMessage(mutation.error)
      : undefined

  return (
    <section className="mx-auto max-w-sm">
      <h1 className="text-2xl font-bold">Create an account</h1>
      <form
        noValidate
        className="mt-6 flex flex-col gap-4"
        onSubmit={form.handleSubmit((values) => mutation.mutate(values))}
      >
        <FormError message={formError} />
        <TextField
          label="Email"
          type="email"
          autoComplete="email"
          error={errors.email?.message}
          {...form.register('email')}
        />
        <TextField
          label="Display name"
          autoComplete="nickname"
          hint="Shown on your comments and reviews."
          error={errors.display_name?.message}
          {...form.register('display_name')}
        />
        <TextField
          label="Password"
          type="password"
          autoComplete="new-password"
          hint={`At least ${PASSWORD_MIN_LENGTH} characters.`}
          error={errors.password?.message}
          {...form.register('password')}
        />
        <Button type="submit" disabled={mutation.isPending}>
          {mutation.isPending ? 'Creating account…' : 'Create account'}
        </Button>
      </form>
      <p className="mt-4 text-sm text-slate-600">
        Already have an account?{' '}
        <Link to="/login" search={{ redirect: redirectTo }} className="font-medium text-indigo-700 underline">
          Sign in
        </Link>
      </p>
    </section>
  )
}
