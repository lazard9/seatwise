import type { ComponentProps } from 'react'

type Variant = 'primary' | 'secondary' | 'text'

const VARIANTS: Record<Variant, string> = {
  primary: 'bg-ink px-4 py-2 text-paper hover:bg-accent',
  secondary: 'border border-ink px-4 py-2 text-ink hover:bg-ink hover:text-paper',
  // Reads as a link; for actions in running text and the header.
  text: 'text-small text-ink hover:underline hover:underline-offset-4',
}

interface ButtonProps extends ComponentProps<'button'> {
  variant?: Variant
}

export function Button({ variant = 'primary', className = '', type = 'button', ...props }: ButtonProps) {
  return (
    <button
      type={type}
      className={`font-medium disabled:cursor-not-allowed disabled:opacity-60 ${VARIANTS[variant]} ${className}`}
      {...props}
    />
  )
}
