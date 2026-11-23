import { z } from 'zod'

// Mirrors the backend rules (app/models/users.py, app/models/auth.py). The backend stays authoritative.
export const PASSWORD_MIN_LENGTH = 8
export const PASSWORD_MAX_LENGTH = 128
export const DISPLAY_NAME_MIN_LENGTH = 2
export const DISPLAY_NAME_MAX_LENGTH = 50

export const loginSchema = z.object({
  email: z.string().trim().min(1, 'Enter your email address.'),
  password: z.string().min(1, 'Enter your password.').max(PASSWORD_MAX_LENGTH),
})

export const registerSchema = z.object({
  email: z.string().trim().pipe(z.email('Enter a valid email address.')),
  display_name: z
    .string()
    .trim()
    .min(DISPLAY_NAME_MIN_LENGTH, `Use at least ${DISPLAY_NAME_MIN_LENGTH} characters.`)
    .max(DISPLAY_NAME_MAX_LENGTH, `Use at most ${DISPLAY_NAME_MAX_LENGTH} characters.`),
  password: z
    .string()
    .min(PASSWORD_MIN_LENGTH, `Use at least ${PASSWORD_MIN_LENGTH} characters.`)
    .max(PASSWORD_MAX_LENGTH, `Use at most ${PASSWORD_MAX_LENGTH} characters.`),
})

export type LoginValues = z.infer<typeof loginSchema>
export type RegisterValues = z.infer<typeof registerSchema>

/** `?redirect=` on /login and /register. Checked again with `safeRedirect` before use. */
export const authSearchSchema = z.object({
  redirect: z.string().optional().catch(undefined),
})

/**
 * Only a path on this site. `//evil.example` and `https://...` would send the
 * user to another site after signing in.
 */
export function safeRedirect(target: string | undefined): string {
  if (!target || !target.startsWith('/') || target.startsWith('//') || target.startsWith('/\\')) {
    return '/'
  }
  return target
}
