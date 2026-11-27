import { describe, expect, it } from 'vitest'
import { alignStepSeries } from './stepSeries'

describe('alignStepSeries', () => {
  it('gives every series the union of the timestamps and holds each value until its next entry', () => {
    const hourly = [{ x: 0, y: 10 }, { x: 4, y: 20 }]
    const quarter = [{ x: 0, y: 1 }, { x: 1, y: 2 }, { x: 2, y: 3 }]
    const [a, b] = alignStepSeries([hourly, quarter])
    expect(a.map((p) => p.x)).toEqual([0, 1, 2, 4])
    expect(a.map((p) => p.y)).toEqual([10, 10, 10, 20])
    expect(b.map((p) => p.y)).toEqual([1, 2, 3, 3])
  })

  it('leaves a gap before a series starts', () => {
    const [late] = alignStepSeries([[{ x: 5, y: 7 }], [{ x: 1, y: 1 }, { x: 5, y: 2 }]])
    expect(late.map((p) => p.y)).toEqual([Number.NaN, 7])
  })

  it('is empty for no data', () => {
    expect(alignStepSeries([[], []])).toEqual([[], []])
  })
})
