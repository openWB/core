export interface PricePoint {
  x: number;
  y: number;
}

export function pricePoints(values: unknown): PricePoint[] {
  if (!values || typeof values !== 'object' || Array.isArray(values)) return [];
  return Object.entries(values)
    .flatMap(([timestamp, value]) => {
      const x = /^\d+$/.test(timestamp)
        ? Number(timestamp) * 1000
        : Date.parse(timestamp);
      if (
        !Number.isFinite(x) ||
        (typeof value !== 'number' && typeof value !== 'string') ||
        (typeof value === 'string' && !value.trim())
      )
        return [];
      // MQTT publishes EUR/Wh; the status page displays ct/kWh.
      const y = Number(value) * 100_000;
      return Number.isFinite(y) ? [{ x, y }] : [];
    })
    .sort((a, b) => a.x - b.x);
}

export function priceIntervalEnd(points: PricePoint[]): number | null {
  const last = points.at(-1);
  if (!last) return null;
  const previous = points.at(-2);
  if (previous) return last.x + (last.x - previous.x);
  // With only one interval, its duration is unknown: use the local day end,
  // matching the status page instead of extending it indefinitely.
  const end = new Date(last.x);
  end.setHours(24, 0, 0, 0);
  return end.getTime();
}

export function currentPrice(points: PricePoint[], now: number): number | null {
  const end = priceIntervalEnd(points);
  if (end === null || now >= end) return null;
  return points.findLast((point) => point.x <= now)?.y ?? null;
}

export function steppedPrices(
  points: PricePoint[],
  limit?: number,
): PricePoint[] {
  const filtered =
    limit === undefined ? points : points.filter((p) => p.x < limit);
  const end = priceIntervalEnd(filtered);
  if (end === null) return [];
  const last = filtered[filtered.length - 1];
  return [...filtered, { x: Math.min(end, limit ?? end) - 1, y: last.y }];
}
