/** A form-level error, announced as soon as it appears. */
export function FormError({ message }: { message: string | undefined }) {
  if (!message) {
    return null
  }
  return (
    <p role="alert" className="rounded-md border border-red-200 bg-red-50 px-3 py-2 text-sm text-red-800">
      {message}
    </p>
  )
}
