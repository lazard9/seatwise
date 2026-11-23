import { isAxiosError } from 'axios'

import type { ApiErrorBody } from '../api/types'

function isErrorBody(value: unknown): value is ApiErrorBody {
  return (
    typeof value === 'object' &&
    value !== null &&
    typeof (value as Record<string, unknown>).code === 'string' &&
    typeof (value as Record<string, unknown>).detail === 'string'
  )
}

/** The domain error `code`, or undefined for network errors and validation (422) errors. */
export function apiErrorCode(error: unknown): string | undefined {
  if (isAxiosError(error) && isErrorBody(error.response?.data)) {
    return error.response.data.code
  }
  return undefined
}

/** Messages for the codes the UI shows. Everything else gets a generic message. */
const MESSAGES: Record<string, string> = {
  INVALID_CREDENTIALS: 'Email or password is incorrect.',
  EMAIL_TAKEN: 'An account with this email already exists.',
  CANNOT_CHANGE_OWN_ROLE: 'You cannot change your own role.',
  USER_NOT_FOUND: 'This user no longer exists.',
  FORBIDDEN_ROLE: 'You do not have permission to do this.',
}

export function apiErrorMessage(error: unknown): string {
  const code = apiErrorCode(error)
  if (code && code in MESSAGES) {
    return MESSAGES[code] ?? ''
  }
  if (isAxiosError(error) && !error.response) {
    return 'Cannot reach the server. Check your connection and try again.'
  }
  return 'Something went wrong. Please try again.'
}
