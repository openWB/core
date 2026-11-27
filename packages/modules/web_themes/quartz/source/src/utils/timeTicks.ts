// visible span (min) -> tick step (min); wider views use hours
const TICK_STEPS = [
  { maxSpanMinutes: 20, stepMinutes: 2 },
  { maxSpanMinutes: 120, stepMinutes: 5 },
  { maxSpanMinutes: 300, stepMinutes: 15 },
  { maxSpanMinutes: 720, stepMinutes: 30 },
]

/** Tick step in minutes for a visible time span in ms, or undefined for hourly ticks. */
export function tickStepMinutes(spanMs: number): number | undefined {
  return TICK_STEPS.find((s) => spanMs <= s.maxSpanMinutes * 60_000)?.stepMinutes
}

/** Round clock times (multiples of `stepMinutes`, local time) within [min, max], as ms timestamps. */
export function roundTimeTicks(min: number, max: number, stepMinutes: number): number[] {
  const first = new Date(min)
  first.setSeconds(0, 0)
  first.setMinutes(Math.ceil(first.getMinutes() / stepMinutes) * stepMinutes)
  if (first.getTime() < min) first.setMinutes(first.getMinutes() + stepMinutes)
  const ticks: number[] = []
  for (let t = first.getTime(); t <= max; t += stepMinutes * 60_000) ticks.push(t)
  return ticks
}
