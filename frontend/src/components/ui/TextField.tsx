import { type ComponentProps, useId } from 'react'

interface TextFieldProps extends ComponentProps<'input'> {
  label: string
  error?: string | undefined
  hint?: string
}

/** A labelled input. The error is announced and linked to the input for screen readers. */
export function TextField({ label, error, hint, ref, ...inputProps }: TextFieldProps) {
  const id = useId()
  const hintId = `${id}-hint`
  const errorId = `${id}-error`
  const describedBy = [hint ? hintId : null, error ? errorId : null].filter(Boolean).join(' ')

  return (
    <div className="flex flex-col gap-1">
      <label htmlFor={id} className="text-sm font-medium text-ink">
        {label}
      </label>
      <input
        id={id}
        ref={ref}
        aria-invalid={error ? true : undefined}
        aria-describedby={describedBy || undefined}
        className="border border-rule bg-transparent px-3 py-2 text-ink aria-invalid:border-danger"
        {...inputProps}
      />
      {hint && (
        <p id={hintId} className="text-sm text-muted">
          {hint}
        </p>
      )}
      {error && (
        <p id={errorId} className="text-sm text-danger">
          {error}
        </p>
      )}
    </div>
  )
}
