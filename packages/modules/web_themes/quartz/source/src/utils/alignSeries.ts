import type { InstancePoint } from '@/types/chart'

/** One point per shared timestamp (NaN = gap), so the 'index' tooltip lines up late-starting series. */
export function alignSeries(points: InstancePoint[], timestamps: number[]): InstancePoint[] {
  if (points.length === timestamps.length && points.every((p, i) => p.timestamp === timestamps[i])) return points
  const byTime = new Map(points.map((p) => [p.timestamp, p.power]))
  return timestamps.map((timestamp) => ({ timestamp, power: byTime.get(timestamp) ?? NaN }))
}
