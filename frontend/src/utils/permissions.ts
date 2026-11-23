import type { Role, User } from '../api/types'

/**
 * The permission matrix from the brief (section 7), for the UI. It decides
 * what to show; the backend decides what is allowed. Keep the two in step.
 *
 * Ownership rows take the owner's id from the resource, e.g. an event's
 * `organizer_id` or a comment's `user_id`.
 */
export type Viewer = Pick<User, 'id' | 'role'> | null

const is = (viewer: Viewer, ...roles: Role[]): boolean =>
  viewer !== null && roles.includes(viewer.role)

const isAdmin = (viewer: Viewer): boolean => is(viewer, 'admin')

/** An organizer acting on their own event. */
const ownsEvent = (viewer: Viewer, organizerId: string): boolean =>
  is(viewer, 'organizer') && viewer?.id === organizerId

export const permissions = {
  createEvent: (viewer: Viewer) => is(viewer, 'admin', 'organizer'),
  uploadImage: (viewer: Viewer) => is(viewer, 'admin', 'organizer'),
  seeDrafts: (viewer: Viewer, organizerId: string) =>
    isAdmin(viewer) || ownsEvent(viewer, organizerId),
  editEvent: (viewer: Viewer, organizerId: string) =>
    isAdmin(viewer) || ownsEvent(viewer, organizerId),
  cancelEvent: (viewer: Viewer, organizerId: string) =>
    isAdmin(viewer) || ownsEvent(viewer, organizerId),
  deleteEvent: (viewer: Viewer) => isAdmin(viewer),
  /** Organizers reserve and review only other organizers' events. */
  reserve: (viewer: Viewer, organizerId: string) =>
    viewer !== null && !ownsEvent(viewer, organizerId),
  cancelOwnReservation: (viewer: Viewer) => viewer !== null,
  seeEventReservations: (viewer: Viewer, organizerId: string) =>
    isAdmin(viewer) || ownsEvent(viewer, organizerId),
  /** Whether the viewer attended is checked by the backend. */
  review: (viewer: Viewer, organizerId: string) =>
    viewer !== null && !ownsEvent(viewer, organizerId),
  favorite: (viewer: Viewer) => viewer !== null,
  comment: (viewer: Viewer) => viewer !== null,
  editOwnContent: (viewer: Viewer, authorId: string) => viewer !== null && viewer.id === authorId,
  /** Authors delete their own comments and reviews; admins delete any. */
  deleteContent: (viewer: Viewer, authorId: string) =>
    isAdmin(viewer) || (viewer !== null && viewer.id === authorId),
  moderateComments: (viewer: Viewer, organizerId: string) =>
    isAdmin(viewer) || ownsEvent(viewer, organizerId),
  manageUsers: (viewer: Viewer) => isAdmin(viewer),
}
