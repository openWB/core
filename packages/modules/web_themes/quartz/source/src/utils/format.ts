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

/** Chart tooltip title for an hour:minute point in time, e.g. a Chart.js x value in ms. */
export function formatTooltipTime(timestamp: number): string {
  return new Date(timestamp).toLocaleTimeString('de-DE', { hour: '2-digit', minute: '2-digit' })
}

/** Format a runtime duration already in seconds, e.g. 5400 -> "1:30 h". */
export function formatRuntime(seconds: number): string {
  const totalMinutes = Math.floor(seconds / 60)
  const hours = Math.floor(totalMinutes / 60)
  const minutes = totalMinutes % 60
  return `${hours}:${String(minutes).padStart(2, '0')} h`
}
