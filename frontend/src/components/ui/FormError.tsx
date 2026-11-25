/** A form-level error, announced as soon as it appears. */
export function FormError({ message }: { message: string | undefined }) {
  if (!message) {
    return null
  }
  return (
    <p role="alert" className="border-l-2 border-danger pl-3 text-small text-danger">
      {message}
    </p>
  )
}
