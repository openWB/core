import { forecastRange } from '../forecastChart/forecast-data';
import type { ForecastPoint } from '../forecastChart/forecast-data';
import { priceIntervalEnd } from '../electricityPriceChart/price-data';
import type { PricePoint } from '../electricityPriceChart/price-data';

export function commonOutlookRange(
  forecast: ForecastPoint[],
  prices: PricePoint[],
  now: number,
): { start: number; end: number } | null {
  const firstForecast = forecast[0];
  const lastForecast = forecast.at(-1);
  const firstPrice = prices[0];
  const priceEnd = priceIntervalEnd(prices);
  if (!firstForecast || !lastForecast || !firstPrice || priceEnd === null)
    return null;

  const days = forecastRange(now);
  const start = Math.max(days.start, firstForecast.x, firstPrice.x);
  // PV values are point samples; prices remain valid through the last interval.
  // Do not extrapolate the PV curve beyond its last actual forecast point.
  const end = Math.min(days.end - 1, lastForecast.x, priceEnd - 1);
  return start < end ? { start, end } : null;
}

export function outlookRange(
  forecast: ForecastPoint[],
  prices: PricePoint[],
  now: number,
  forecastConfigured: boolean,
  pricesConfigured: boolean,
): { start: number; end: number } | null {
  if (forecastConfigured && pricesConfigured)
    return commonOutlookRange(forecast, prices, now);

  if (forecastConfigured) {
    const first = forecast[0];
    const last = forecast.at(-1);
    if (!first || !last) return null;
    const days = forecastRange(now);
    const start = Math.max(days.start, first.x);
    const end = Math.min(days.end - 1, last.x);
    return start < end ? { start, end } : null;
  }

  if (pricesConfigured) {
    const first = prices[0];
    const end = priceIntervalEnd(prices);
    return first && end !== null && first.x < end - 1
      ? { start: first.x, end: end - 1 }
      : null;
  }
  return null;
}
