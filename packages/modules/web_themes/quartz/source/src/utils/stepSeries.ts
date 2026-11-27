export interface XY {
  x: number
  y: number
}

/** Puts stepped series on the union of their timestamps: Chart.js' 'index' tooltip pairs datasets by array position. NaN before a series' first entry. Series must be sorted by x. */
export function alignStepSeries(series: XY[][]): XY[][] {
  const xs = [...new Set(series.flatMap((s) => s.map((p) => p.x)))].sort((a, b) => a - b)
  return series.map((s) => {
    let i = -1
    return xs.map((x) => {
      while (i + 1 < s.length && s[i + 1].x <= x) i++
      return { x, y: i >= 0 ? s[i].y : Number.NaN }
    })
  })
}
