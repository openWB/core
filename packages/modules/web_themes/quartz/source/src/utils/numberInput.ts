/** The number in an input, or `previous` if it holds nothing usable (Number('') is 0, which would save a 0 when the field was only cleared). min and max are clamped because the attributes do not stop typed values. */
export function parseNumberInput(raw: string, previous: number, min?: number, max?: number): number {
  const text = raw.trim().replace(',', '.')
  if (text === '') return previous
  const value = Number(text)
  if (!Number.isFinite(value)) return previous
  let result = value
  if (min !== undefined) result = Math.max(min, result)
  if (max !== undefined) result = Math.min(max, result)
  return result
}
