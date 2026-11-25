import type { Category } from '../../api/types'
import { CATEGORY_NAMES } from '../../utils/format'

interface EventArtProps {
  image: string | null
  category: Category
  /** 4:5 on cards, 16:9 on the event page. */
  shape?: 'portrait' | 'wide'
  showLabel?: boolean
}

/** The event image, or the category's motif when there is none. Decorative: the title is beside it. */
export function EventArt({ image, category, shape = 'portrait', showLabel = false }: EventArtProps) {
  const ratio = shape === 'portrait' ? 'aspect-[4/5]' : 'aspect-video'
  if (image) {
    return (
      <img
        src={image}
        alt=""
        loading="lazy"
        className={`${ratio} w-full max-w-full bg-field object-cover`}
      />
    )
  }
  return (
    <div
      aria-hidden="true"
      className={`motif-${category} relative ${ratio} w-full max-w-full overflow-hidden bg-field`}
    >
      {showLabel && (
        <span className="eyebrow absolute bottom-2 left-2.5 bg-paper px-1 text-ink">
          {CATEGORY_NAMES[category]}
        </span>
      )}
    </div>
  )
}
