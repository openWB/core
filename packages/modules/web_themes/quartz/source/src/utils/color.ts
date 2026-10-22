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
