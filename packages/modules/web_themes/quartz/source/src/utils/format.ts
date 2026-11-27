export function formatKw(kw: number): string {
  const watts = Math.round(kw * 1000) || 0 // || 0 turns -0 into 0
  if (Math.abs(watts) < 1000) return `${watts.toLocaleString()} W`
  return `${kw.toLocaleString(undefined, { minimumFractionDigits: 3, maximumFractionDigits: 3 })} kW`
}

export function formatCentsPerKwh(cents: number): string {
  return `${cents.toLocaleString(undefined, { minimumFractionDigits: 1, maximumFractionDigits: 1 })} ct`
}

export function formatKwh(kwh: number, decimals = 3): string {
  return `${kwh.toLocaleString(undefined, { minimumFractionDigits: decimals, maximumFractionDigits: decimals })} kWh`
}

/** The backend stores prices in EUR/Wh, the UI shows ct/kWh. Rounded because *100000/100000 is not exact in floating point (0.0003 gives 29.999999999999996). */
export function eurPerWhToCtPerKwh(eurPerWh: number): number {
  return Math.round(eurPerWh * 100000 * 1000) / 1000
}
export function ctPerKwhToEurPerWh(ctPerKwh: number): number {
  return ctPerKwh / 100000
}

/** DC charging is set as a current like AC but shown as a power, assuming 3 phases at 230 V. */
export function convertDcCurrentToPower(dcCurrent: number): number {
  return Math.round((dcCurrent * 3 * 230) / 1000)
}
export function convertPowerToDcCurrent(power: number): number {
  return Math.round((power * 1000) / (230 * 3))
}

export function formatTooltipTime(timestamp: number, seconds = false): string {
  return new Date(timestamp).toLocaleTimeString('de-DE', {
    hour: '2-digit',
    minute: '2-digit',
    second: seconds ? '2-digit' : undefined,
  })
}

export function formatChartDateLabel(date: Date): string {
  const startOfDay = (d: Date) => new Date(d).setHours(0, 0, 0, 0)
  const diffDays = Math.round((startOfDay(date) - startOfDay(new Date())) / 86_400_000)
  if (diffDays === 0) return 'Heute'
  if (diffDays === -1) return 'Gestern'
  return date.toLocaleDateString('de-DE', { weekday: 'short', day: '2-digit', month: '2-digit' })
}

export function formatRuntime(seconds: number): string {
  const totalMinutes = Math.floor(seconds / 60)
  const hours = Math.floor(totalMinutes / 60)
  const minutes = totalMinutes % 60
  return `${hours}:${String(minutes).padStart(2, '0')} h`
}
