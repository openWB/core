import { afterEach, describe, expect, it, vi } from 'vitest';
import { forecastNumber, forecastPoints, forecastRange } from './forecast-data';

afterEach(() => vi.unstubAllEnvs());

describe('PV forecast data', () => {
  it('sorts Unix seconds and ISO times, converts watts to kW, and retains zero', () => {
    const now = new Date(2026, 10, 13, 12).getTime();
    const { start } = forecastRange(now);
    expect(
      forecastPoints(
        {
          [String(start / 1000 + 7200)]: '12590',
          [new Date(start + 3600_000).toISOString()]: 2000,
          [String(start / 1000)]: 0,
        },
        now,
      ),
    ).toEqual([
      { x: start, y: 0 },
      { x: start + 3600_000, y: 2 },
      { x: start + 7200_000, y: 12.59 },
    ]);
  });

  it('excludes other days and malformed or missing values without inventing zeros', () => {
    const now = new Date(2026, 10, 13, 12).getTime();
    const { start, end } = forecastRange(now);
    expect(
      forecastPoints(
        {
          [String(start / 1000 - 1)]: 1200,
          [String(end / 1000)]: 1200,
          [String(start / 1000)]: null,
          [String(start / 1000 + 3600)]: '',
          [String(start / 1000 + 7200)]: -100,
          invalid: 1200,
        },
        now,
      ),
    ).toEqual([]);
    expect(forecastPoints([], now)).toEqual([]);
    expect(forecastNumber(null)).toBeNull();
    expect(forecastNumber('')).toBeNull();
    expect(forecastNumber(Infinity)).toBeNull();
    expect(forecastNumber(0)).toBe(0);
  });

  it('uses two local calendar days across daylight-saving changes', () => {
    vi.stubEnv('TZ', 'Europe/Berlin');
    const spring = forecastRange(new Date(2026, 2, 28, 12).getTime());
    const autumn = forecastRange(new Date(2026, 9, 24, 12).getTime());
    expect((spring.end - spring.start) / 3600_000).toBe(47);
    expect((autumn.end - autumn.start) / 3600_000).toBe(49);
    expect(new Date(spring.end).getHours()).toBe(0);
    expect(new Date(autumn.end).getHours()).toBe(0);
  });
});
