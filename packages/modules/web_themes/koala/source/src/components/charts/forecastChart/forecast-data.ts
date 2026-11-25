export interface ForecastPoint {
  x: number;
  y: number;
}

export function forecastRange(now: number): { start: number; end: number } {
  const start = new Date(now);
  start.setHours(0, 0, 0, 0);
  const end = new Date(start);
  end.setDate(end.getDate() + 2);
  return { start: start.getTime(), end: end.getTime() };
}

export function forecastPoints(values: unknown, now: number): ForecastPoint[] {
  if (!values || typeof values !== 'object' || Array.isArray(values)) return [];
  const { start, end } = forecastRange(now);
  return Object.entries(values)
    .flatMap(([timestamp, power]) => {
      // Providers publish Unix seconds; the backend also supports ISO timestamps.
      const x = /^\d+$/.test(timestamp)
        ? Number(timestamp) * 1000
        : Date.parse(timestamp);
      const y = forecastNumber(power);
      return Number.isFinite(x) && x >= start && x < end && y !== null && y >= 0
        ? [{ x, y: y / 1000 }]
        : [];
    })
    .sort((a, b) => a.x - b.x);
}

export function forecastNumber(value: unknown): number | null {
  if (typeof value !== 'number' && typeof value !== 'string') return null;
  if (typeof value === 'string' && !value.trim()) return null;
  const number = Number(value);
  return Number.isFinite(number) ? number : null;
}
