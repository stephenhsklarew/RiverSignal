/** Convert Celsius to Fahrenheit, rounded to 1 decimal. */
export function cToF(c: number): number {
  return Math.round((c * 9 / 5 + 32) * 10) / 10
}

/** Format a Celsius value as Fahrenheit string. */
export function tempF(c: number | null | undefined): string {
  if (c == null) return '—'
  return `${cToF(c)}°F`
}
