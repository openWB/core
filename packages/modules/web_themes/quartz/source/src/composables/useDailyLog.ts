import { computed, onMounted, onUnmounted, ref, watch } from 'vue'
import { useMqttStore } from '@/stores/mqtt-store'
import type {
  CategoryData,
  CategoryKey,
  InstancePoint,
  InstanceSeries,
  SocCategoryData,
  SocPoint,
  SocSeries,
} from '@/types/chart'

/** One flow's energy in/out of a daily_log component entry, already in kW (see process_log.py::convert_legacy_units). */
interface FlowEntry {
  power_imported?: number
  power_exported?: number
  grid?: boolean
  soc?: number
}

/** Keyed by vehicle id (e.g. "ev1") - see process_log_entry_builder.py's ev_dict, a sibling of bat/cp/pv/consumer. */
interface VehicleLogEntry {
  soc?: number
}

interface DailyLogEntry {
  timestamp: number
  counter?: Record<string, FlowEntry>
  pv?: Record<string, FlowEntry>
  bat?: Record<string, FlowEntry>
  cp?: Record<string, FlowEntry>
  consumer?: Record<string, FlowEntry>
  hc?: Record<string, FlowEntry>
  ev?: Record<string, VehicleLogEntry>
}

interface DailyLogResponse {
  entries: DailyLogEntry[]
  names?: Record<string, string>
  /** PV forecast for this day, keyed by timestamp (seconds) -> power (W) - see write_log.py::get_forecast_values. */
  forecast?: Record<string, number>
}

function dateToString(date: Date): string {
  return (
    date.getFullYear().toString() +
    (date.getMonth() + 1).toString().padStart(2, '0') +
    date.getDate().toString().padStart(2, '0')
  )
}

function startOfDay(date: Date): Date {
  const d = new Date(date)
  d.setHours(0, 0, 0, 0)
  return d
}

type SignMode = 'export' | 'import' | 'net'

function flowValue(flow: FlowEntry | undefined, mode: SignMode): number {
  if (!flow) return 0
  if (mode === 'export') return flow.power_exported ?? 0
  if (mode === 'import') return flow.power_imported ?? 0
  return (flow.power_imported ?? 0) - (flow.power_exported ?? 0)
}

/** Builds a category's combined ('all') series plus one series per other instance key in that group. */
function buildCategory(
  entries: DailyLogEntry[],
  group: 'pv' | 'bat' | 'cp' | 'consumer',
  mode: SignMode,
  names: Record<string, string>,
  fallbackLabel: string,
): CategoryData {
  const all: InstancePoint[] = []
  const instancePoints = new Map<string, InstancePoint[]>()

  entries.forEach((entry) => {
    const timestamp = entry.timestamp * 1000
    const groupData = entry[group] ?? {}
    all.push({ timestamp, power: flowValue(groupData.all, mode) })
    Object.keys(groupData).forEach((id) => {
      if (id === 'all') return
      if (!instancePoints.has(id)) instancePoints.set(id, [])
      instancePoints.get(id)?.push({ timestamp, power: flowValue(groupData[id], mode) })
    })
  })

  const individual: InstanceSeries[] = Array.from(instancePoints.entries()).map(([id, points]) => ({
    id,
    label: names[id] ?? `${fallbackLabel} ${id.replace(/\D/g, '')}`,
    points,
  }))
  return { all, individual }
}

/** Grid/house have no meaningful per-instance breakdown - there's only one grid connection / one house total. */
function buildCombinedOnly(points: InstancePoint[]): CategoryData {
  return { all: points, individual: [] }
}

function gridPower(entry: DailyLogEntry): number {
  let imported = 0
  let exported = 0
  Object.values(entry.counter ?? {}).forEach((counter) => {
    if (counter.grid) {
      imported += counter.power_imported ?? 0
      exported += counter.power_exported ?? 0
    }
  })
  return imported - exported
}

/**
 * Non-grid counters (sub-meters a user adds for monitoring - a wallbox circuit, a heat pump,
 * etc.) have no 'all' aggregate key in the log (unlike pv/bat/cp/consumer), so their combined
 * series is built by summing every counter entry except the one flagged 'grid' (already
 * covered by gridPower/the 'grid' category).
 */
function buildCounterCategory(entries: DailyLogEntry[], names: Record<string, string>): CategoryData {
  const all: InstancePoint[] = []
  const instancePoints = new Map<string, InstancePoint[]>()

  entries.forEach((entry) => {
    const timestamp = entry.timestamp * 1000
    let sum = 0
    Object.entries(entry.counter ?? {}).forEach(([id, flow]) => {
      if (flow.grid) return
      const value = flowValue(flow, 'net')
      sum += value
      if (!instancePoints.has(id)) instancePoints.set(id, [])
      instancePoints.get(id)?.push({ timestamp, power: value })
    })
    all.push({ timestamp, power: sum })
  })

  const individual: InstanceSeries[] = Array.from(instancePoints.entries()).map(([id, points]) => ({
    id,
    label: names[id] ?? `Zähler ${id.replace(/\D/g, '')}`,
    points,
  }))
  return { all, individual }
}

function buildBatterySoc(entries: DailyLogEntry[], names: Record<string, string>): SocCategoryData {
  const all: SocPoint[] = []
  const instancePoints = new Map<string, SocPoint[]>()

  entries.forEach((entry) => {
    const timestamp = entry.timestamp * 1000
    const batData = entry.bat ?? {}
    if (batData.all?.soc !== undefined) all.push({ timestamp, soc: batData.all.soc })
    Object.keys(batData).forEach((id) => {
      if (id === 'all') return
      const soc = batData[id].soc
      if (soc === undefined) return
      if (!instancePoints.has(id)) instancePoints.set(id, [])
      instancePoints.get(id)?.push({ timestamp, soc })
    })
  })

  const individual: SocSeries[] = Array.from(instancePoints.entries()).map(([id, points]) => ({
    id,
    label: names[id] ?? `Speicher ${id.replace(/\D/g, '')}`,
    points,
  }))
  return { all, individual }
}

/** Same unit conversion as mqttStore.forecastSeries (W -> kW), so both feed the chart identically. */
function buildForecast(log: DailyLogResponse | undefined): InstancePoint[] {
  return Object.entries(log?.forecast ?? {})
    .map(([timestamp, watts]) => ({ timestamp: Number(timestamp) * 1000, power: watts / 1000 }))
    .sort((a, b) => a.timestamp - b.timestamp)
}

function buildVehicleSoc(entries: DailyLogEntry[], names: Record<string, string>): SocSeries[] {
  const instancePoints = new Map<string, SocPoint[]>()
  entries.forEach((entry) => {
    const timestamp = entry.timestamp * 1000
    Object.entries(entry.ev ?? {}).forEach(([id, ev]) => {
      if (ev.soc === undefined) return
      if (!instancePoints.has(id)) instancePoints.set(id, [])
      instancePoints.get(id)?.push({ timestamp, soc: ev.soc })
    })
  })
  return Array.from(instancePoints.entries()).map(([id, points]) => ({
    id: id.replace(/\D/g, ''),
    label: names[id] ?? `Fahrzeug ${id.replace(/\D/g, '')}`,
    points,
  }))
}

/**
 * Fetches and parses a day's daily_log into per-category chart series, kept live via the
 * getDailyLog command. Defaults to today and auto-follows the real date across midnight, unless
 * the caller has navigated to a past day via goToPreviousDay/goToNextDay (goToToday re-enables
 * following).
 */
export function useDailyLog() {
  const mqttStore = useMqttStore()
  const selectedDate = ref(startOfDay(new Date()))
  const followToday = ref(true)
  const dateString = computed(() => dateToString(selectedDate.value))
  const topic = computed(() => `openWB/log/daily/${dateString.value}`)
  const isToday = computed(() => dateString.value === dateToString(new Date()))

  function goToPreviousDay(): void {
    followToday.value = false
    const d = new Date(selectedDate.value)
    d.setDate(d.getDate() - 1)
    selectedDate.value = d
  }
  function goToNextDay(): void {
    const d = new Date(selectedDate.value)
    d.setDate(d.getDate() + 1)
    const today = startOfDay(new Date())
    if (d.getTime() >= today.getTime()) {
      followToday.value = true
      selectedDate.value = today
    } else {
      selectedDate.value = d
    }
  }
  function goToToday(): void {
    followToday.value = true
    selectedDate.value = startOfDay(new Date())
  }

  const categories = computed<Record<CategoryKey, CategoryData>>(() => {
    const log = mqttStore.getValue<DailyLogResponse | undefined>(topic.value, undefined)
    const entries = log?.entries ?? []
    const names = log?.names ?? {}
    return {
      pv: buildCategory(entries, 'pv', 'export', names, 'Wechselrichter'),
      battery: buildCategory(entries, 'bat', 'net', names, 'Speicher'),
      chargepoint: buildCategory(entries, 'cp', 'import', names, 'Ladepunkt'),
      consumer: buildCategory(entries, 'consumer', 'import', names, 'Verbraucher'),
      grid: buildCombinedOnly(entries.map((e) => ({ timestamp: e.timestamp * 1000, power: gridPower(e) }))),
      house: buildCombinedOnly(
        entries.map((e) => ({ timestamp: e.timestamp * 1000, power: flowValue(e.hc?.all, 'import') })),
      ),
      counter: buildCounterCategory(entries, names),
    }
  })

  const batterySoc = computed<SocCategoryData>(() => {
    const log = mqttStore.getValue<DailyLogResponse | undefined>(topic.value, undefined)
    return buildBatterySoc(log?.entries ?? [], log?.names ?? {})
  })
  const vehicleSocAll = computed<SocSeries[]>(() => {
    const log = mqttStore.getValue<DailyLogResponse | undefined>(topic.value, undefined)
    return buildVehicleSoc(log?.entries ?? [], log?.names ?? {})
  })
  const forecast = computed<InstancePoint[]>(() =>
    buildForecast(mqttStore.getValue<DailyLogResponse | undefined>(topic.value, undefined)),
  )

  const hasData = computed(() => categories.value.grid.all.length > 0)

  // swap the subscription and request fresh data whenever the topic itself changes (date
  // navigation, or the date rolling over at midnight) - fires once immediately to establish the
  // initial subscription, same idiom useLiveView's mode-driven subscribe/unsubscribe already uses
  watch(
    topic,
    (newTopic, oldTopic) => {
      if (oldTopic) mqttStore.unsubscribe(oldTopic)
      mqttStore.subscribe(newTopic)
      mqttStore.fetchDailyLog(selectedDate.value)
    },
    { immediate: true },
  )

  // the backend only republishes this retained topic in response to a getDailyLog command - it
  // doesn't push updates on its own, so without a periodic re-fetch today's chart would go stale;
  // a past day's log is already complete and never changes, so it's left alone. While following
  // today, this is also what carries selectedDate across midnight instead of freezing on
  // yesterday's date forever.
  const REFRESH_INTERVAL_MS = 60_000
  let refreshTimer: ReturnType<typeof setInterval> | undefined

  onMounted(() => {
    refreshTimer = setInterval(() => {
      if (!followToday.value) return
      selectedDate.value = startOfDay(new Date())
      mqttStore.fetchDailyLog(selectedDate.value)
    }, REFRESH_INTERVAL_MS)
  })
  onUnmounted(() => {
    mqttStore.unsubscribe(topic.value)
    clearInterval(refreshTimer)
  })

  return {
    categories,
    hasData,
    batterySoc,
    vehicleSocAll,
    forecast,
    selectedDate,
    isToday,
    goToPreviousDay,
    goToNextDay,
    goToToday,
  }
}
