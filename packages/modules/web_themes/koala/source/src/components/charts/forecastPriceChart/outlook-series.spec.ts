import { describe, expect, it } from 'vitest';
import {
  forecastValueAt,
  outlookTimeline,
  forecastOnTimeline,
  pricesOnTimeline,
} from './outlook-series';

const hour = 3_600_000;
const forecast = [
  { x: 0, y: 0 },
  { x: hour, y: 4 },
  { x: 2 * hour, y: 2 },
];

describe('synchronized PV and price readouts', () => {
  it('interpolates the displayed PV curve instead of holding the previous hourly value', () => {
    expect(forecastValueAt(forecast, hour / 4)).toBe(1);
    expect(forecastValueAt(forecast, hour / 2)).toBe(2);
    expect(forecastValueAt(forecast, 1.5 * hour)).toBe(3);
    expect(forecastValueAt(forecast, 0)).toBe(0);
    expect(forecastValueAt(forecast, hour)).toBe(4);
  });

  it('never extrapolates missing PV values beyond the actual forecast', () => {
    expect(forecastValueAt(forecast, -1)).toBeNull();
    expect(forecastValueAt(forecast, 2 * hour + 1)).toBeNull();
    expect(forecastValueAt([], hour)).toBeNull();
  });

  it('pairs hour-based PV with quarter-hour tariffs at every tooltip index', () => {
    const prices = [0, 0.25, 0.5, 0.75].map((h, i) => ({
      x: h * hour,
      y: [10, 20, -5, 30][i],
    }));
    const timeline = outlookTimeline(
      forecast,
      [prices],
      { start: 0, end: hour - 1 },
      0,
    );
    const pv = forecastOnTimeline(forecast, timeline),
      tariff = pricesOnTimeline(prices, timeline);
    expect(pv.map((p) => p.x)).toEqual(tariff.map((p) => p.x));
    expect(pv.slice(0, 4).map((p) => p.y)).toEqual([0, 1, 2, 3]);
    expect(tariff.slice(0, 4).map((p) => p.y)).toEqual([10, 20, -5, 30]);
    expect(pv.every((p) => Number.isFinite(p.y))).toBe(true);
  });

  it('includes the current time so the summary and tooltip use the exact same PV value', () => {
    const now = hour / 3;
    const timeline = outlookTimeline(
      forecast,
      [],
      { start: 0, end: hour },
      now,
    );
    const pv = forecastOnTimeline(forecast, timeline);
    expect(pv.find((p) => p.x === now)?.y).toBe(forecastValueAt(forecast, now));
    expect(timeline).toEqual([0, now, hour]);
    expect(outlookTimeline(forecast, [], null, now)).toEqual([]);
  });

  it('preserves interval boundaries and does not invent zeros for unavailable components', () => {
    const prices = [
      { x: 0, y: 0 },
      { x: hour / 4, y: -2 },
    ];
    const timeline = outlookTimeline(
      forecast,
      [prices],
      { start: 0, end: hour },
      0,
    );
    const sampled = pricesOnTimeline(prices, timeline);
    expect(sampled.find((p) => p.x === hour / 2 - 1)?.y).toBe(-2);
    expect(sampled.find((p) => p.x === hour / 2)?.y).toBeNaN();
    expect(sampled.find((p) => p.x === 0)?.y).toBe(0);
    expect(forecastOnTimeline([], [0])[0].y).toBeNaN();
  });
});
