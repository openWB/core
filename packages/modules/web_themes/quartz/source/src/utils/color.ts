/** Resolve a CSS custom property to its current literal value - canvas drawing can't use var(--x) directly. */
export function getCssColor(name: string, fallback = '#888888'): string {
  const value = getComputedStyle(document.documentElement).getPropertyValue(name).trim()
  return value || fallback
}

export function hexToRgba(hex: string, opacity = 1): string {
  const value = hex.replace('#', '')
  const num = parseInt(value, 16)
  const r = (num >> 16) & 255
  const g = (num >> 8) & 255
  const b = num & 255
  return `rgba(${r}, ${g}, ${b}, ${opacity})`
}

/** Lighten (positive) or darken (negative) a hex color by a percentage, clamped to a valid channel range. */
export function shadeColor(hex: string, percent: number): string {
  const num = parseInt(hex.replace('#', ''), 16)
  const amount = Math.round((percent / 100) * 255)
  const clamp = (channel: number) => Math.min(255, Math.max(0, channel + amount))
  const r = clamp((num >> 16) & 255)
  const g = clamp((num >> 8) & 255)
  const b = clamp(num & 255)
  return `#${((1 << 24) + (r << 16) + (g << 8) + b).toString(16).slice(1)}`
}

/** A distinguishable shade of a category's base color for its Nth individual-instance line, same base color always. */
export function instanceColor(baseHex: string, index: number): string {
  const steps = [0, -25, 25, -45, 45, -60, 60]
  return shadeColor(baseHex, steps[index % steps.length])
}
