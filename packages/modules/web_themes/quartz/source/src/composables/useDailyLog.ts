import { computed, onMounted, onUnmounted } from 'vue'
import { useMqttStore } from '@/stores/mqtt-store'
import type { CategoryData, CategoryKey, InstancePoint, InstanceSeries } from '@/types/chart'

/** One flow's energy in/out of a daily_log component entry, already in kW (see process_log.py::convert_legacy_units). */
interface FlowEntry {
  power_imported?: number
  power_exported?: number
  grid?: boolean
}

interface DailyLogEntry {
  timestamp: number
  counter?: Record<string, FlowEntry>
  pv?: Record<string, FlowEntry>
  bat?: Record<string, FlowEntry>
  cp?: Record<string, FlowEntry>
  consumer?: Record<string, FlowEntry>
  hc?: Record<string, FlowEntry>
}

interface DailyLogResponse {
  entries: DailyLogEntry[]
  names?: Record<string, string>
}

function todayDateString(): string {
  const now = new Date()
  return (
    now.getFullYear().toString() +
    (now.getMonth() + 1).toString().padStart(2, '0') +
    now.getDate().toString().padStart(2, '0')
  )
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

/** Fetches and parses today's daily_log into per-category chart series, kept live via the getDailyLog command. */
export function useDailyLog() {
  const mqttStore = useMqttStore()
  const dateString = todayDateString()
  const topic = `openWB/log/daily/${dateString}`

  const categories = computed<Record<CategoryKey, CategoryData>>(() => {
    const log = mqttStore.getValue<DailyLogResponse | undefined>(topic, undefined)
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

  const hasData = computed(() => categories.value.grid.all.length > 0)

  // the backend only republishes this retained topic in response to a getDailyLog command - it
  // doesn't push updates on its own, so without a periodic re-fetch the chart would go stale
  const REFRESH_INTERVAL_MS = 60_000
  let refreshTimer: ReturnType<typeof setInterval> | undefined

  onMounted(() => {
    mqttStore.fetchDailyLog()
    refreshTimer = setInterval(() => mqttStore.fetchDailyLog(), REFRESH_INTERVAL_MS)
  })
  onUnmounted(() => {
    mqttStore.unsubscribe(topic)
    clearInterval(refreshTimer)
  })

  return { categories, hasData }
}
