import { describe, expect, it } from 'vitest'
import { localDateString, nextRunDate, setFrequency, withDefaultWeekday } from './planSchedule'

const weekly = (...days: number[]) => Array.from({ length: 7 }, (_, i) => days.includes(i))
// Friday 2026-11-27
const at = (h: number, m: number) => new Date(2026, 10, 27, h, m)

describe('localDateString', () => {
  it('is the local day, also shortly after midnight', () => {
    expect(localDateString(at(0, 30))).toBe('2026-11-27')
  })
})

describe('nextRunDate', () => {
  it('daily: today while the time is still coming, otherwise tomorrow', () => {
    const daily = { selected: 'daily' as const, once: '', weekly: weekly() }
    expect(nextRunDate(daily, '07:00', at(6, 59))).toBe('2026-11-27')
    expect(nextRunDate(daily, '07:00', at(7, 0))).toBe('2026-11-28')
  })

  it('weekly: the next selected weekday, today only if its time has not passed', () => {
    const fridayMonday = { selected: 'weekly' as const, once: '', weekly: weekly(0, 4) }
    expect(nextRunDate(fridayMonday, '18:00', at(12, 0))).toBe('2026-11-27')
    expect(nextRunDate(fridayMonday, '18:00', at(19, 0))).toBe('2026-11-30')
  })

  it('weekly: a plan for only today\'s weekday and a passed time runs next week', () => {
    expect(nextRunDate({ selected: 'weekly', once: '', weekly: weekly(4) }, '08:00', at(9, 0))).toBe('2026-12-04')
  })

  it('weekly without a day and once without a date have no next run', () => {
    expect(nextRunDate({ selected: 'weekly', once: '', weekly: weekly() }, '08:00', at(9, 0))).toBeUndefined()
    expect(nextRunDate({ selected: 'once', once: '', weekly: weekly() }, '08:00', at(9, 0))).toBeUndefined()
  })

  it('once: the given date', () => {
    expect(nextRunDate({ selected: 'once', once: '2026-12-24', weekly: weekly() }, '08:00', at(9, 0))).toBe('2026-12-24')
  })
})

describe('withDefaultWeekday', () => {
  it('selects today when no day is selected', () => {
    expect(withDefaultWeekday(weekly(), at(10, 0))).toEqual(weekly(4)) // Friday
  })

  it('keeps an existing selection', () => {
    const selected = weekly(0, 2)
    expect(withDefaultWeekday(selected, at(10, 0))).toBe(selected)
  })
})

describe('setFrequency', () => {
  it('selects today when switching to weekly without a day', () => {
    const frequency = { selected: 'daily' as const, weekly: weekly() }
    setFrequency(frequency, 'weekly', at(10, 0))
    expect(frequency).toEqual({ selected: 'weekly', weekly: weekly(4) })
  })

  it('leaves the days alone for the other choices and for a weekly plan that has days', () => {
    const frequency = { selected: 'weekly' as const, weekly: weekly(1) }
    setFrequency(frequency, 'daily', at(10, 0))
    expect(frequency.weekly).toEqual(weekly(1))
    setFrequency(frequency, 'weekly', at(10, 0))
    expect(frequency.weekly).toEqual(weekly(1))
  })
})
