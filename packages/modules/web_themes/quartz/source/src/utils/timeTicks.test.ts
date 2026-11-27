import { describe, expect, it } from 'vitest'
import { roundTimeTicks, tickStepMinutes } from './timeTicks'

const at = (h: number, m: number, s = 0) => new Date(2026, 10, 23, h, m, s).getTime()
const clock = (ts: number) => new Date(ts).toTimeString().slice(0, 5)

describe('tickStepMinutes', () => {
  it('picks the step by visible span, boundaries included', () => {
    expect(tickStepMinutes(20 * 60_000)).toBe(2)
    expect(tickStepMinutes(21 * 60_000)).toBe(5)
    expect(tickStepMinutes(120 * 60_000)).toBe(5)
    expect(tickStepMinutes(300 * 60_000)).toBe(15)
    expect(tickStepMinutes(720 * 60_000)).toBe(30)
  })
  it('returns undefined (hours) for wider views', () => {
    expect(tickStepMinutes(721 * 60_000)).toBeUndefined()
  })
})

describe('roundTimeTicks', () => {
  it('starts on the next round time, not at the left edge', () => {
    expect(roundTimeTicks(at(9, 3), at(9, 21), 5).map(clock)).toEqual(['09:05', '09:10', '09:15', '09:20'])
  })
  it('includes an edge that is already a round time', () => {
    expect(roundTimeTicks(at(9, 0), at(9, 30), 15).map(clock)).toEqual(['09:00', '09:15', '09:30'])
  })
  it('skips an edge on a round minute with leftover seconds', () => {
    expect(roundTimeTicks(at(9, 15, 30), at(9, 45), 15).map(clock)).toEqual(['09:30', '09:45'])
  })
  it('rolls over the hour', () => {
    expect(roundTimeTicks(at(9, 50), at(10, 10), 10).map(clock)).toEqual(['09:50', '10:00', '10:10'])
  })
})
