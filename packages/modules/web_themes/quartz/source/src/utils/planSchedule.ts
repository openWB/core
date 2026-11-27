/** Local YYYY-MM-DD (toISOString would give the UTC day). */
export function localDateString(date: Date): string {
  const month = String(date.getMonth() + 1).padStart(2, '0')
  const day = String(date.getDate()).padStart(2, '0')
  return `${date.getFullYear()}-${month}-${day}`
}

export function formatDateDDMMYYYY(dateString: string): string {
  const [year, month, day] = dateString.split('-')
  return `${day}.${month}.${year}`
}

interface Recurrence {
  selected: 'daily' | 'weekly' | 'once'
  once: string
  weekly: boolean[]
}

/** The local day a plan runs next; today only while its time has not passed. weekly is Mo=0..So=6. undefined for a weekly plan without a day or a once plan without a date. */
export function nextRunDate(frequency: Recurrence, time: string, now: Date): string | undefined {
  if (frequency.selected === 'once') return frequency.once || undefined
  const [hours, minutes] = time.split(':').map(Number)
  const todayStillComing = now.getHours() * 60 + now.getMinutes() < hours * 60 + minutes
  for (let offset = 0; offset <= 7; offset++) {
    if (offset === 0 && !todayStillComing) continue
    const day = new Date(now.getFullYear(), now.getMonth(), now.getDate() + offset)
    const weekdayIndex = (day.getDay() + 6) % 7
    if (frequency.selected === 'daily' || frequency.weekly[weekdayIndex]) return localDateString(day)
  }
  return undefined
}

/** A weekly recurrence without a day never runs, so today's weekday is selected. */
export function withDefaultWeekday(weekly: boolean[], now: Date): boolean[] {
  if (weekly.some(Boolean)) return weekly
  const next = [...weekly]
  next[(now.getDay() + 6) % 7] = true
  return next
}

/** "weekly" selects today's weekday when none is set. */
export function setFrequency(
  frequency: { selected: 'daily' | 'weekly' | 'once'; weekly: boolean[] },
  selected: 'daily' | 'weekly' | 'once',
  now = new Date(),
): void {
  frequency.selected = selected
  if (selected === 'weekly') frequency.weekly = withDefaultWeekday(frequency.weekly, now)
}
