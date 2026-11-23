import { describe, expect, it } from 'vitest'

import { permissions, type Viewer } from './permissions'

// One viewer per column of the matrix. "Own" resources belong to the organizer.
const admin: Viewer = { id: 'u-admin', role: 'admin' }
const organizer: Viewer = { id: 'u-org', role: 'organizer' }
const otherOrganizer: Viewer = { id: 'u-org-2', role: 'organizer' }
const attendee: Viewer = { id: 'u-att', role: 'attendee' }
const anonymous: Viewer = null

const OWN_EVENT = 'u-org'

type Row = [string, (viewer: Viewer) => boolean, [boolean, boolean, boolean, boolean, boolean]]

// Columns: admin, organizer on own event, organizer on another's event, attendee, anonymous.
const MATRIX: Row[] = [
  ['create event', (v) => permissions.createEvent(v), [true, true, true, false, false]],
  ['upload image', (v) => permissions.uploadImage(v), [true, true, true, false, false]],
  ['see drafts', (v) => permissions.seeDrafts(v, OWN_EVENT), [true, true, false, false, false]],
  ['edit event', (v) => permissions.editEvent(v, OWN_EVENT), [true, true, false, false, false]],
  ['cancel event', (v) => permissions.cancelEvent(v, OWN_EVENT), [true, true, false, false, false]],
  ['delete event', (v) => permissions.deleteEvent(v), [true, false, false, false, false]],
  ['reserve seats', (v) => permissions.reserve(v, OWN_EVENT), [true, false, true, true, false]],
  [
    'cancel own reservation',
    (v) => permissions.cancelOwnReservation(v),
    [true, true, true, true, false],
  ],
  [
    'see reservations for an event',
    (v) => permissions.seeEventReservations(v, OWN_EVENT),
    [true, true, false, false, false],
  ],
  ['review', (v) => permissions.review(v, OWN_EVENT), [true, false, true, true, false]],
  ['favorite', (v) => permissions.favorite(v), [true, true, true, true, false]],
  ['comment', (v) => permissions.comment(v), [true, true, true, true, false]],
  [
    'hide or unhide comments',
    (v) => permissions.moderateComments(v, OWN_EVENT),
    [true, true, false, false, false],
  ],
  ['manage users and roles', (v) => permissions.manageUsers(v), [true, false, false, false, false]],
]

const VIEWERS: [string, Viewer][] = [
  ['admin', admin],
  ['organizer (own event)', organizer],
  ["organizer (another's event)", otherOrganizer],
  ['attendee', attendee],
  ['anonymous', anonymous],
]

describe.each(MATRIX)('%s', (_action, check, expected) => {
  it.each(VIEWERS.map(([name, viewer], i) => [name, viewer, expected[i]] as const))(
    '%s: %s',
    (_name, viewer, allowed) => {
      expect(check(viewer)).toBe(allowed)
    },
  )
})

describe('own content', () => {
  it('only the author edits a comment or review', () => {
    expect(permissions.editOwnContent(attendee, 'u-att')).toBe(true)
    expect(permissions.editOwnContent(attendee, 'someone-else')).toBe(false)
    expect(permissions.editOwnContent(admin, 'u-att')).toBe(false)
    expect(permissions.editOwnContent(anonymous, 'u-att')).toBe(false)
  })

  it('the author or an admin deletes it', () => {
    expect(permissions.deleteContent(attendee, 'u-att')).toBe(true)
    expect(permissions.deleteContent(admin, 'u-att')).toBe(true)
    expect(permissions.deleteContent(organizer, 'u-att')).toBe(false)
    expect(permissions.deleteContent(anonymous, 'u-att')).toBe(false)
  })
})
