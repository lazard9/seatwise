import { AxiosError, AxiosHeaders } from 'axios'
import { describe, expect, it } from 'vitest'

import { apiErrorCode, apiErrorMessage } from './apiErrors'

function httpError(status: number, data: unknown): AxiosError {
  const config = { headers: new AxiosHeaders() }
  return new AxiosError('failed', 'ERR_BAD_RESPONSE', config, null, {
    status,
    statusText: '',
    headers: {},
    config,
    data,
  })
}

describe('api errors', () => {
  it('reads the domain code', () => {
    const error = httpError(409, { detail: 'taken', code: 'EMAIL_TAKEN' })

    expect(apiErrorCode(error)).toBe('EMAIL_TAKEN')
    expect(apiErrorMessage(error)).toBe('An account with this email already exists.')
  })

  it('has no code for validation errors and shows a generic message', () => {
    const error = httpError(422, { detail: [{ msg: 'bad' }] })

    expect(apiErrorCode(error)).toBeUndefined()
    expect(apiErrorMessage(error)).toBe('Something went wrong. Please try again.')
  })

  it('explains a network error', () => {
    const error = new AxiosError('Network Error', 'ERR_NETWORK')

    expect(apiErrorMessage(error)).toMatch(/cannot reach the server/i)
  })

  it('never shows the server detail for an unknown code', () => {
    const error = httpError(400, { detail: 'internal wording', code: 'SOMETHING_NEW' })

    expect(apiErrorMessage(error)).not.toContain('internal wording')
  })
})
