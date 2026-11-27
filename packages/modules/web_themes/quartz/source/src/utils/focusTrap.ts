/** Where Tab should go to keep focus in a dialog (wrap around the ends, bring stray focus in), or null to leave it to the browser. */
export function trapTarget<T>(focusable: T[], active: unknown, shift: boolean, container: unknown): T | null {
  if (focusable.length === 0) return null
  const first = focusable[0]
  const last = focusable[focusable.length - 1]
  if (shift && (active === first || active === container)) return last
  if (!shift && active === last) return first
  if (!focusable.includes(active as T) && active !== container) return shift ? last : first
  return null
}

export const FOCUSABLE_SELECTOR =
  'a[href], button:not([disabled]), input:not([disabled]), select:not([disabled]), textarea:not([disabled]), [tabindex]:not([tabindex="-1"])'
