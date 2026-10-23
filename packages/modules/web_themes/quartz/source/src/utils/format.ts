/** Format a power value already in kW, e.g. 6.4 -> "6,400 kW" (3 decimals, matching the other web themes). */
export function formatKw(kw: number): string {
  return `${kw.toLocaleString(undefined, { minimumFractionDigits: 3, maximumFractionDigits: 3 })} kW`
}

/** Format a price in ct/kWh, e.g. 21.4 -> "21,4 ct". */
export function formatCentsPerKwh(cents: number): string {
  return `${cents.toLocaleString(undefined, { minimumFractionDigits: 1, maximumFractionDigits: 1 })} ct`
}
