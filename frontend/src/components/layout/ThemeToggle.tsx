import { useState } from 'react'

type Theme = 'system' | 'light' | 'dark'

const STORAGE_KEY = 'seatwise-theme'
const NEXT: Record<Theme, Theme> = { system: 'dark', dark: 'light', light: 'system' }
const LABEL: Record<Theme, string> = { system: 'Auto', dark: 'Dark', light: 'Light' }

function readTheme(): Theme {
  const value = document.documentElement.dataset.theme
  return value === 'dark' || value === 'light' ? value : 'system'
}

/** Cycles Auto, Dark, Light. The script in index.html applies the choice before first paint. */
export function ThemeToggle() {
  const [theme, setTheme] = useState<Theme>(readTheme)

  function change() {
    const next = NEXT[theme]
    if (next === 'system') {
      delete document.documentElement.dataset.theme
    } else {
      document.documentElement.dataset.theme = next
    }
    try {
      if (next === 'system') localStorage.removeItem(STORAGE_KEY)
      else localStorage.setItem(STORAGE_KEY, next)
    } catch {
      // Storage can be blocked; the choice then lasts until the page is closed.
    }
    setTheme(next)
  }

  return (
    <button
      type="button"
      onClick={change}
      className="eyebrow hover:text-ink"
      aria-label={`Theme: ${LABEL[theme]}. Change theme`}
    >
      {LABEL[theme]}
    </button>
  )
}
