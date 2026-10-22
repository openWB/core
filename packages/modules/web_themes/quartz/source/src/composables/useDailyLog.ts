import { computed, onMounted, onUnmounted } from 'vue'
import { useMqttStore } from '@/stores/mqtt-store'

/** One flow's energy in/out of a daily_log component entry, already in kW (see process_log.py::convert_legacy_units). */
interface FlowEntry {
  power_imported?: number
  power_exported?: number
  soc?: number
  grid?: boolean
}

interface DailyLogEntry {
  timestamp: number
  counter: Record<string, FlowEntry>
  pv: Record<string, FlowEntry>
  bat: Record<string, FlowEntry>
  cp: Record<string, FlowEntry>
  consumer: Record<string, FlowEntry>
  hc?: Record<string, FlowEntry>
  prices?: { grid: number }
}

export interface ChartPoint {
  timestamp: number
  pv: number
  grid: number
  house: number
  battery: number
  consumer: number
}

function todayDateString(): string {
  const now = new Date()
  return (
    now.getFullYear().toString() +
    (now.getMonth() + 1).toString().padStart(2, '0') +
    now.getDate().toString().padStart(2, '0')
  )
}

function toChartPoint(entry: DailyLogEntry): ChartPoint {
  let gridImported = 0
  let gridExported = 0
  Object.values(entry.counter ?? {}).forEach((counter) => {
    if (counter.grid) {
      gridImported += counter.power_imported ?? 0
      gridExported += counter.power_exported ?? 0
    }
  })
  return {
    timestamp: entry.timestamp * 1000,
    pv: entry.pv?.all?.power_exported ?? 0,
    grid: gridImported - gridExported,
    house: entry.hc?.all?.power_imported ?? 0,
    battery: (entry.bat?.all?.power_imported ?? 0) - (entry.bat?.all?.power_exported ?? 0),
    consumer: entry.consumer?.all?.power_imported ?? 0,
  }
}

/** Fetches and parses today's daily_log into chart-ready points, kept live via the getDailyLog command. */
export function useDailyLog() {
  const mqttStore = useMqttStore()
  const dateString = todayDateString()
  const topic = `openWB/log/daily/${dateString}`

  const points = computed<ChartPoint[]>(() => {
    const log = mqttStore.getValue<{ entries: DailyLogEntry[] } | undefined>(topic, undefined)
    return log?.entries.map(toChartPoint).sort((a, b) => a.timestamp - b.timestamp) ?? []
  })

  onMounted(() => mqttStore.fetchDailyLog())
  onUnmounted(() => mqttStore.unsubscribe(topic))

  return { points }
}
