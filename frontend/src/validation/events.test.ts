import { describe, expect, it } from 'vitest'

import { eventsSearchSchema } from './events'

describe('events search params', () => {
  it('keeps valid values', () => {
    const search = {
      page: 2,
      search: 'jazz',
      category: 'music',
      tag: 'open air',
      city: 'Novi Sad',
      from: '2026-12-01',
      to: '2026-12-31',
      free: true,
      seats: true,
      sort: 'price_asc',
      cols: 6,
    }

    expect(eventsSearchSchema.parse(search)).toEqual(search)
  })

  it('drops invalid values instead of failing', () => {
    const parsed = eventsSearchSchema.parse({
      page: -1,
      category: 'opera',
      sort: 'random',
      cols: 5,
      from: '12/01/2026',
      search: '   ',
    })

    expect(parsed).toEqual({})
  })

  it('reads a number the router parsed back as text', () => {
    expect(eventsSearchSchema.parse({ tag: 2026 }).tag).toBe('2026')
  })
})
