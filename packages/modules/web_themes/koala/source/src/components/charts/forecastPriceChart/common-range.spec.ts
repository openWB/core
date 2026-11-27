import { describe, expect, it } from 'vitest';
import { commonOutlookRange, outlookRange } from './common-range';

const start = new Date(2026, 10, 18).getTime();
const hour = 3_600_000;
const point = (hours: number) => ({ x: start + hours * hour, y: 1 });

describe('shared PV forecast and electricity price period', () => {
  it('ends with the final price interval when prices cover less time', () => {
    // Quarter-hour prices explicitly cover today, while PV includes tomorrow.
    const prices = Array.from({ length: 96 }, (_, i) => point(i / 4));
    expect(commonOutlookRange([point(0), point(47)], prices, start)).toEqual({
      start,
      end: start + 24 * hour - 1,
    });
  });

  it('ends at the last real forecast point when PV covers less time', () => {
    expect(
      commonOutlookRange([point(0), point(12)], [point(0), point(23)], start),
    ).toEqual({ start, end: start + 12 * hour });
  });

  it('starts where both series are available, regardless of which begins later', () => {
    expect(
      commonOutlookRange([point(4), point(18)], [point(2), point(20)], start),
    ).toEqual({ start: start + 4 * hour, end: start + 18 * hour });
    expect(
      commonOutlookRange([point(2), point(18)], [point(4), point(20)], start),
    ).toEqual({ start: start + 4 * hour, end: start + 18 * hour });
  });

  it('has no common period if either series is missing or they do not overlap', () => {
    expect(commonOutlookRange([], [point(0)], start)).toBeNull();
    expect(commonOutlookRange([point(0), point(12)], [], start)).toBeNull();
    expect(
      commonOutlookRange([point(0), point(4)], [point(8), point(9)], start),
    ).toBeNull();
    expect(
      commonOutlookRange([point(0), point(8)], [point(8), point(9)], start),
    ).toBeNull();
  });

  it('keeps the overlap inside today and tomorrow, including DST changes', () => {
    const now = new Date(2026, 9, 25).getTime();
    const end = new Date(2026, 9, 27).getTime();
    expect(
      commonOutlookRange(
        [
          { x: now - hour, y: 1 },
          { x: end + hour, y: 1 },
        ],
        [
          { x: now - hour, y: 1 },
          { x: end + hour, y: 1 },
        ],
        now,
      ),
    ).toEqual({ start: now, end: end - 1 });
  });
});

describe('period for individually configured modules', () => {
  const forecast = [point(0), point(47)];
  const prices = Array.from({ length: 96 }, (_, i) => point(i / 4));

  it('shows the full forecast without being limited by disabled price data', () => {
    expect(outlookRange(forecast, [], start, true, false)).toEqual({
      start,
      end: start + 47 * hour,
    });
    expect(outlookRange(forecast, prices, start, true, false)).toEqual({
      start,
      end: start + 47 * hour,
    });
  });

  it('shows all price intervals independently of disabled forecast data', () => {
    expect(outlookRange([], prices, start, false, true)).toEqual({
      start,
      end: start + 24 * hour - 1,
    });
    expect(
      outlookRange([point(8), point(12)], prices, start, false, true),
    ).toEqual({
      start,
      end: start + 24 * hour - 1,
    });
  });

  it('requires the overlap only when both modules are configured', () => {
    expect(outlookRange(forecast, prices, start, true, true)).toEqual({
      start,
      end: start + 24 * hour - 1,
    });
    expect(outlookRange(forecast, [], start, true, true)).toBeNull();
  });

  it('has no period when the selected module has no data or both are disabled', () => {
    expect(outlookRange([], prices, start, true, false)).toBeNull();
    expect(outlookRange(forecast, [], start, false, true)).toBeNull();
    expect(outlookRange(forecast, prices, start, false, false)).toBeNull();
  });
});
