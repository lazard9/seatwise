import { describe, expect, it } from 'vitest'

import { registerSchema, safeRedirect } from './auth'

describe('safeRedirect', () => {
  it.each([
    ['/admin/users?page=2', '/admin/users?page=2'],
    ['/', '/'],
    [undefined, '/'],
    ['', '/'],
    ['//evil.example', '/'],
    ['/\\evil.example', '/'],
    ['https://evil.example', '/'],
    ['javascript:alert(1)', '/'],
  ])('%s -> %s', (input, expected) => {
    expect(safeRedirect(input)).toBe(expected)
  })
})

describe('register schema', () => {
  const valid = { email: 'ana@example.com', display_name: 'Ana', password: 'x'.repeat(8) }

  it('accepts the backend limits exactly', () => {
    expect(registerSchema.safeParse({ ...valid, password: 'x'.repeat(128) }).success).toBe(true)
    expect(registerSchema.safeParse({ ...valid, display_name: 'x'.repeat(50) }).success).toBe(true)
  })

  it('rejects one past each limit', () => {
    expect(registerSchema.safeParse({ ...valid, password: 'x'.repeat(7) }).success).toBe(false)
    expect(registerSchema.safeParse({ ...valid, password: 'x'.repeat(129) }).success).toBe(false)
    expect(registerSchema.safeParse({ ...valid, display_name: 'x' }).success).toBe(false)
    expect(registerSchema.safeParse({ ...valid, display_name: 'x'.repeat(51) }).success).toBe(false)
  })

  it('trims the display name before counting', () => {
    expect(registerSchema.safeParse({ ...valid, display_name: '  A  ' }).success).toBe(false)
  })
})
