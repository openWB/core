import { describe, expect, it } from 'vitest'
import { priceRuns } from './priceRuns'

// slots at 0, 1, 2, 3 and the closing point at 4 (the last price held on)
const series = [
  { x: 0, y: 10 },
  { x: 1, y: 12 },
  { x: 2, y: 30 },
  { x: 3, y: 31 },
  { x: 4, y: 31 },
]

describe('priceRuns', () => {
  it('lets each run end where the next one starts, so no slot stays unshaded', () => {
    expect(priceRuns(series, 20)).toEqual([
      { from: 0, to: 2, allowed: true },
      { from: 2, to: 4, allowed: false },
    ])
  })

  it('is a single run when everything is on one side', () => {
    expect(priceRuns(series, 100)).toEqual([{ from: 0, to: 4, allowed: true }])
    expect(priceRuns(series, 0)).toEqual([{ from: 0, to: 4, allowed: false }])
  })

  it('counts a price equal to the threshold as allowed', () => {
    expect(priceRuns(series, 12)[0]).toEqual({ from: 0, to: 2, allowed: true })
  })
})
