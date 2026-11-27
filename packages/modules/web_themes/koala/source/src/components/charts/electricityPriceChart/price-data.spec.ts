import { describe, expect, it } from 'vitest';
import {
  currentPrice,
  priceIntervalEnd,
  pricePoints,
  steppedPrices,
} from './price-data';

describe('electricity price data', () => {
  it('converts EUR/Wh to ct/kWh, sorts timestamps, and retains zero and negative prices', () => {
    expect(
      pricePoints({
        '1800000900': '-0.00002',
        '1800000000': 0,
        '1800001800': 0.0003123,
      }),
    ).toEqual([
      { x: 1800000000000, y: 0 },
      { x: 1800000900000, y: -2 },
      { x: 1800001800000, y: 31.23 },
    ]);
    expect(
      pricePoints({
        invalid: 1,
        '1800000000': null,
        '1800000900': '',
        '1800001800': Infinity,
      }),
    ).toEqual([]);
    expect(pricePoints(undefined)).toEqual([]);
  });

  it('selects the active quarter-hour interval and rejects future or expired data', () => {
    const points = [
      { x: 0, y: 20 },
      { x: 900_000, y: 30 },
    ];
    expect(currentPrice(points, -1)).toBeNull();
    expect(currentPrice(points, 899_999)).toBe(20);
    expect(currentPrice(points, 900_000)).toBe(30);
    expect(currentPrice(points, 1799_999)).toBe(30);
    expect(currentPrice(points, 1800_000)).toBeNull();
    expect(currentPrice([], 0)).toBeNull();
  });

  it('extends the last step to its interval end and clips components to total-price availability', () => {
    const points = [
      { x: 0, y: 20 },
      { x: 3600_000, y: 30 },
      { x: 7200_000, y: 40 },
    ];
    expect(priceIntervalEnd(points)).toBe(10800_000);
    expect(steppedPrices(points).at(-1)).toEqual({ x: 10799_999, y: 40 });
    expect(steppedPrices(points, 5400_000)).toEqual([
      { x: 0, y: 20 },
      { x: 3600_000, y: 30 },
      { x: 5399_999, y: 30 },
    ]);
    expect(steppedPrices([], 5400_000)).toEqual([]);
    const start = new Date(2026, 10, 16, 23).getTime();
    const end = new Date(2026, 10, 17).getTime();
    expect(priceIntervalEnd([{ x: start, y: 10 }])).toBe(end);
  });
});
