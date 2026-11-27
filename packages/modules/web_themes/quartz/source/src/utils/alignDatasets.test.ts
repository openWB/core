import { describe, expect, it } from 'vitest'
import { alignDatasets } from './alignDatasets'

const ds = (...points: [number, number][]) => ({ data: points.map(([x, y]) => ({ x, y })) })

describe('alignDatasets', () => {
  it('gives every dataset the union of the timestamps, NaN where it has no point', () => {
    const [a, b] = alignDatasets([ds([0, 1], [2, 3]), ds([1, 10], [2, 20])])
    expect(a.data.map((p) => p.x)).toEqual([0, 1, 2])
    expect(b.data.map((p) => p.x)).toEqual([0, 1, 2])
    expect(a.data.map((p) => p.y)).toEqual([1, Number.NaN, 3])
    expect(b.data.map((p) => p.y)).toEqual([Number.NaN, 10, 20])
  })

  it('interpolates a forecast inside its range and leaves it empty outside', () => {
    const power = ds([10, 1], [20, 2], [30, 3])
    const forecast = ds([0, 0], [20, 4], [40, 8])
    const [, aligned] = alignDatasets([power, forecast], new Set([forecast]))
    expect(aligned.data.map((p) => p.x)).toEqual([0, 10, 20, 30, 40])
    expect(aligned.data.map((p) => p.y)).toEqual([0, 2, 4, 6, 8])
  })

  it('does not shift anything for forecast points before the first log entry (system started mid-day)', () => {
    const power = ds([100, 5], [200, 6])
    const forecast = ds([0, 1], [50, 2], [100, 3], [200, 4], [300, 5])
    const [p, f] = alignDatasets([power, forecast], new Set([forecast]))
    // same index = same time in both
    expect(p.data.map((q) => q.x)).toEqual(f.data.map((q) => q.x))
    const at100 = p.data.findIndex((q) => q.x === 100)
    expect(p.data[at100].y).toBe(5)
    expect(f.data[at100].y).toBe(3)
  })

  it('lets the lines run across the gaps and keeps empty datasets empty', () => {
    const [a, empty] = alignDatasets([ds([0, 1]), ds()])
    expect(a.spanGaps).toBe(true)
    expect(empty.data.every((p) => Number.isNaN(p.y))).toBe(true)
  })

  // a forecast every 15 minutes next to log entries every 5 minutes: no stop that has only the forecast
  it('does not add forecast timestamps inside the range of the other datasets', () => {
    const power = ds([0, 1], [5, 2], [10, 3], [20, 5])
    const forecast = ds([0, 0], [15, 30], [30, 60])
    const [, aligned] = alignDatasets([power, forecast], new Set([forecast]))
    expect(aligned.data.map((p) => p.x)).toEqual([0, 5, 10, 20, 30])
    expect(aligned.data.map((p) => p.y)).toEqual([0, 10, 20, 40, 60])
  })

  it('works when there is only a forecast', () => {
    const forecast = ds([0, 1], [10, 2])
    const [aligned] = alignDatasets([forecast], new Set([forecast]))
    expect(aligned.data.map((p) => p.x)).toEqual([0, 10])
  })
})
