export interface PricePoint {
  x: number
  y: number
}

export interface PriceRun {
  from: number
  to: number
  allowed: boolean
}

/** Runs of slots at or below the threshold (allowed) or above it (blocked). A run ends where the next starts, since a price holds until the next point. */
export function priceRuns(series: PricePoint[], threshold: number): PriceRun[] {
  const runs: PriceRun[] = []
  let runStart = 0
  for (let i = 1; i <= series.length; i++) {
    const runAllowed = series[runStart].y <= threshold
    if (i === series.length || series[i].y <= threshold !== runAllowed) {
      runs.push({ from: series[runStart].x, to: i < series.length ? series[i].x : series[i - 1].x, allowed: runAllowed })
      runStart = i
    }
  }
  return runs
}
