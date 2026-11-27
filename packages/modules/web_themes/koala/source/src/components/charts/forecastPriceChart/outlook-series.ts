import type { ForecastPoint } from '../forecastChart/forecast-data';
import {
  currentPrice,
  priceIntervalEnd,
} from '../electricityPriceChart/price-data';
import type { PricePoint } from '../electricityPriceChart/price-data';

// The displayed PV line and all readouts use the same piecewise-linear curve.
export function forecastValueAt(
  points: ForecastPoint[],
  timestamp: number,
): number | null {
  const right = points.findIndex((point) => point.x >= timestamp);
  if (right < 0) return null;
  const next = points[right];
  if (next.x === timestamp) return next.y;
  if (right === 0) return null;
  const previous = points[right - 1];
  const fraction = (timestamp - previous.x) / (next.x - previous.x);
  return previous.y + fraction * (next.y - previous.y);
}

export function outlookTimeline(
  forecast: ForecastPoint[],
  prices: PricePoint[][],
  range: { start: number; end: number } | null,
  now: number,
): number[] {
  if (!range) return [];
  const times = [
    range.start,
    range.end,
    now,
    ...forecast.map((point) => point.x),
  ];
  for (const series of prices) {
    times.push(...series.map((point) => point.x));
    const end = priceIntervalEnd(series);
    // Preserve the last price interval and mark where an optional series ends.
    if (end !== null) times.push(end - 1, end);
  }
  return [...new Set(times)]
    .filter((timestamp) => timestamp >= range.start && timestamp <= range.end)
    .sort((a, b) => a - b);
}

export function forecastOnTimeline(
  points: ForecastPoint[],
  timeline: number[],
): ForecastPoint[] {
  // Chart.js skips NaN values instead of treating unavailable data as zero.
  return timeline.map((x) => ({ x, y: forecastValueAt(points, x) ?? NaN }));
}

export function pricesOnTimeline(
  points: PricePoint[],
  timeline: number[],
): PricePoint[] {
  return timeline.map((x) => ({ x, y: currentPrice(points, x) ?? NaN }));
}
