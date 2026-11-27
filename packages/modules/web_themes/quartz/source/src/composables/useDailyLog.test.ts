import { describe, expect, it } from 'vitest'
import { DAILY_LOG_REFRESH_MS, dailyLogRefreshDue } from './useDailyLog'

const base = { followToday: true, hidden: false, lastFetchAt: 1_000_000, now: 1_000_000 }

describe('dailyLogRefreshDue', () => {
  it('waits for the full interval', () => {
    expect(dailyLogRefreshDue({ ...base, now: base.lastFetchAt + DAILY_LOG_REFRESH_MS - 1 })).toBe(false)
    expect(dailyLogRefreshDue({ ...base, now: base.lastFetchAt + DAILY_LOG_REFRESH_MS })).toBe(true)
  })

  it('never asks for a hidden tab or a past day', () => {
    const later = base.lastFetchAt + 10 * DAILY_LOG_REFRESH_MS
    expect(dailyLogRefreshDue({ ...base, now: later, hidden: true })).toBe(false)
    expect(dailyLogRefreshDue({ ...base, now: later, followToday: false })).toBe(false)
  })

  it('is due again as soon as a long-hidden tab is shown', () => {
    expect(dailyLogRefreshDue({ ...base, now: base.lastFetchAt + 3 * 60 * 60_000 })).toBe(true)
  })
})
