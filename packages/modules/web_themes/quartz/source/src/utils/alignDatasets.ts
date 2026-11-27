import type { XY } from './stepSeries'

/**
 * Puts all datasets of a time chart on the same timestamps, so that Chart.js' 'index' tooltip, which pairs datasets
 * by array position, always compares values of the same time. A dataset has NaN where it has no point.
 * The `interpolated` ones (a forecast with other timestamps than the log) are interpolated linearly inside their own
 * range. Their own timestamps only count outside the range of the other datasets: inside it they would add stops where
 * the tooltip shows the forecast alone. Lines run across the gaps (`spanGaps`). Every dataset must be sorted by x.
 */
export function alignDatasets<D extends { data: XY[] }>(
  datasets: D[],
  interpolated: ReadonlySet<D> = new Set(),
): (D & { spanGaps: boolean })[] {
  const timestamps = (list: D[]) => list.flatMap((d) => d.data.map((p) => p.x))
  const fixed = timestamps(datasets.filter((d) => !interpolated.has(d)))
  const first = Math.min(...fixed)
  const last = Math.max(...fixed)
  const outside = timestamps(datasets.filter((d) => interpolated.has(d))).filter((x) => x < first || x > last)
  const xs = [...new Set([...fixed, ...outside])].sort((a, b) => a - b)
  return datasets.map((dataset) => {
    const points = dataset.data
    const byX = new Map(points.map((p) => [p.x, p.y]))
    let i = 0
    const data = xs.map((x) => {
      const exact = byX.get(x)
      if (exact !== undefined) return { x, y: exact }
      if (!interpolated.has(dataset) || points.length === 0 || x < points[0].x || x > points[points.length - 1].x) {
        return { x, y: Number.NaN }
      }
      while (i + 1 < points.length && points[i + 1].x <= x) i++
      const a = points[i]
      const b = points[i + 1]
      return { x, y: a.y + ((b.y - a.y) * (x - a.x)) / (b.x - a.x) }
    })
    return { ...dataset, data, spanGaps: true }
  })
}
