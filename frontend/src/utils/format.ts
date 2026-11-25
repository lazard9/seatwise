import type { Category } from '../api/types'

/** Events happen in Serbia, so their times are shown in Belgrade time wherever you are. */
export const EVENT_TIME_ZONE = 'Europe/Belgrade'

const priceFormat = new Intl.NumberFormat('sr-RS', { maximumFractionDigits: 2 })

/** `Free` for 0, otherwise the amount in RSD with Serbian digit grouping: `1.500 RSD`. */
export function formatPrice(price: number): string {
  return price === 0 ? 'Free' : `${priceFormat.format(price)} RSD`
}

const dayFormat = new Intl.DateTimeFormat('en-GB', {
  weekday: 'short',
  day: 'numeric',
  month: 'short',
  timeZone: EVENT_TIME_ZONE,
})
const dayWithYearFormat = new Intl.DateTimeFormat('en-GB', {
  weekday: 'short',
  day: 'numeric',
  month: 'short',
  year: 'numeric',
  timeZone: EVENT_TIME_ZONE,
})
const timeFormat = new Intl.DateTimeFormat('en-GB', {
  hour: '2-digit',
  minute: '2-digit',
  hourCycle: 'h23',
  timeZone: EVENT_TIME_ZONE,
})
const yearFormat = new Intl.DateTimeFormat('en-GB', { year: 'numeric', timeZone: EVENT_TIME_ZONE })

function day(date: Date, now: Date): string {
  // The year only when it is not this year.
  const sameYear = yearFormat.format(date) === yearFormat.format(now)
  return (sameYear ? dayFormat : dayWithYearFormat).format(date).replace(',', '')
}

/** `Fri 12 Dec · 20:00`, for cards. */
export function formatEventStart(iso: string, now = new Date()): string {
  const date = new Date(iso)
  return `${day(date, now)} · ${timeFormat.format(date)}`
}

/** `Fri 12 Dec 2026, 20:00 to 23:00`, or both days when the event runs past midnight. */
export function formatEventRange(startIso: string, endIso: string): string {
  const start = new Date(startIso)
  const end = new Date(endIso)
  const startDay = dayWithYearFormat.format(start).replace(',', '')
  const endDay = dayWithYearFormat.format(end).replace(',', '')
  if (startDay === endDay) {
    return `${startDay}, ${timeFormat.format(start)} to ${timeFormat.format(end)}`
  }
  return `${startDay}, ${timeFormat.format(start)} to ${endDay}, ${timeFormat.format(end)}`
}

export const CATEGORY_LABELS: Record<Category, string> = {
  music: 'Music',
  theatre: 'Theatre',
  talk: 'Talks',
  workshop: 'Workshops',
  sport: 'Sport',
  festival: 'Festivals',
  other: 'Other',
}

/** Singular, for one event: `Talk`, not `Talks`. */
export const CATEGORY_NAMES: Record<Category, string> = {
  music: 'Music',
  theatre: 'Theatre',
  talk: 'Talk',
  workshop: 'Workshop',
  sport: 'Sport',
  festival: 'Festival',
  other: 'Other',
}

/** Start of a local calendar day as an ISO time with an offset, for `date_from`. */
export function startOfDayIso(day: string): string {
  return new Date(`${day}T00:00:00`).toISOString()
}

/** End of a local calendar day, for `date_to`. */
export function endOfDayIso(day: string): string {
  return new Date(`${day}T23:59:59.999`).toISOString()
}
