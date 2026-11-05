/** Format a power value already in kW, e.g. 6.4 -> "6,400 kW" (3 decimals, matching the other web themes). */
export function formatKw(kw: number): string {
  return `${kw.toLocaleString(undefined, { minimumFractionDigits: 3, maximumFractionDigits: 3 })} kW`
}

/** Format a price in ct/kWh, e.g. 21.4 -> "21,4 ct". */
export function formatCentsPerKwh(cents: number): string {
  return `${cents.toLocaleString(undefined, { minimumFractionDigits: 1, maximumFractionDigits: 1 })} ct`
}

/** Format an energy value already in kWh, e.g. 6.4 -> "6,400 kWh" (3 decimals, matching formatKw). */
export function formatKwh(kwh: number): string {
  return `${kwh.toLocaleString(undefined, { minimumFractionDigits: 3, maximumFractionDigits: 3 })} kWh`
}

/**
 * The backend stores variable electricity prices as EUR/Wh; every price field in the UI displays
 * ct/kWh instead (x100000). Rounded to 3 decimals (matching the UI's own 0.001 step) since the
 * raw *100000/100000 round-trip isn't exact in floating point (e.g. 0.0003 -> 29.999999999999996
 * unrounded) - centralized here so every price field converts the same way instead of each
 * reimplementing (and potentially missing) the rounding.
 */
export function eurPerWhToCtPerKwh(eurPerWh: number): number {
  return Math.round(eurPerWh * 100000 * 1000) / 1000
}
export function ctPerKwhToEurPerWh(ctPerKwh: number): number {
  return ctPerKwh / 100000
}

/** Chart tooltip title for an hour:minute point in time, e.g. a Chart.js x value in ms. */
export function formatTooltipTime(timestamp: number): string {
  return new Date(timestamp).toLocaleTimeString('de-DE', { hour: '2-digit', minute: '2-digit' })
}

/** Day-view chart heading, e.g. "Heute", "Gestern", or "Mo., 03.11.". */
export function formatChartDateLabel(date: Date): string {
  const startOfDay = (d: Date) => new Date(d).setHours(0, 0, 0, 0)
  const diffDays = Math.round((startOfDay(date) - startOfDay(new Date())) / 86_400_000)
  if (diffDays === 0) return 'Heute'
  if (diffDays === -1) return 'Gestern'
  return date.toLocaleDateString('de-DE', { weekday: 'short', day: '2-digit', month: '2-digit' })
}

/** Format a runtime duration already in seconds, e.g. 5400 -> "1:30 h". */
export function formatRuntime(seconds: number): string {
  const totalMinutes = Math.floor(seconds / 60)
  const hours = Math.floor(totalMinutes / 60)
  const minutes = totalMinutes % 60
  return `${hours}:${String(minutes).padStart(2, '0')} h`
}
