import { describe, expect, it } from 'vitest'

import { formatEventRange, formatEventStart, formatPrice } from './format'

describe('formatPrice', () => {
  it.each([
    [0, 'Free'],
    [1500, '1.500 RSD'],
    [800, '800 RSD'],
    [1250.5, '1.250,5 RSD'],
  ])('%s gives %s', (price, text) => {
    expect(formatPrice(price)).toBe(text)
  })
})

describe('event dates, in Belgrade time', () => {
  const now = new Date('2026-11-25T12:00:00Z')

  it('shows a card date without the year when it is this year', () => {
    // 19:00 UTC is 20:00 in Belgrade in winter.
    expect(formatEventStart('2026-12-12T19:00:00Z', now)).toBe('Sat 12 Dec · 20:00')
  })

  it('adds the year when it is another year', () => {
    expect(formatEventStart('2027-01-03T11:00:00Z', now)).toBe('Sun 3 Jan 2027 · 12:00')
  })

  it('shows one day with two times for an evening event', () => {
    expect(formatEventRange('2026-12-12T19:00:00Z', '2026-12-12T22:00:00Z')).toBe(
      'Sat 12 Dec 2026, 20:00 to 23:00',
    )
  })

  it('shows both days when the event runs past midnight', () => {
    expect(formatEventRange('2026-12-12T21:00:00Z', '2026-12-13T01:00:00Z')).toBe(
      'Sat 12 Dec 2026, 22:00 to Sun 13 Dec 2026, 02:00',
    )
  })
})
