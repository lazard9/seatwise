import type { ComponentProps } from 'react'

type Variant = 'primary' | 'secondary'

const VARIANTS: Record<Variant, string> = {
  primary: 'bg-indigo-700 text-white hover:bg-indigo-800',
  secondary: 'border border-slate-300 bg-white text-slate-900 hover:bg-slate-50',
}

interface ButtonProps extends ComponentProps<'button'> {
  variant?: Variant
}

export function Button({ variant = 'primary', className = '', type = 'button', ...props }: ButtonProps) {
  return (
    <button
      type={type}
      className={`rounded-md px-4 py-2 font-medium disabled:cursor-not-allowed disabled:opacity-60 ${VARIANTS[variant]} ${className}`}
      {...props}
    />
  )
}
