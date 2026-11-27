import { computed, onMounted, onUnmounted, ref, watch, type Ref } from 'vue'
import { alignSeries } from '@/utils/alignSeries'
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

/** Values are in kW (see process_log.py::convert_legacy_units). */
interface FlowEntry {
  power_imported?: number
  power_exported?: number
  grid?: boolean
  soc?: number
}

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
  /** The forecast (W) as it stood at this entry's timestamp. */
  forecast?: number | null
}

interface DailyLogResponse {
  entries: DailyLogEntry[]
  names?: Record<string, string>
}

function instanceNumber(id: string): number {
  return Number(id.replace(/\D/g, ''))
}

function entryTimestamps(entries: DailyLogEntry[]): number[] {
  return entries.map((entry) => entry.timestamp * 1000)
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

function buildCategory(
  entries: DailyLogEntry[],
  group: 'pv' | 'bat' | 'cp' | 'consumer',
  mode: SignMode,
  names: Record<string, string>,
  fallbackLabel: string,
  // when given, only these instances count and 'all' is their sum
  include?: (id: string) => boolean,
): CategoryData {
  const all: InstancePoint[] = []
  const instancePoints = new Map<string, InstancePoint[]>()

  entries.forEach((entry) => {
    const timestamp = entry.timestamp * 1000
    const groupData = entry[group] ?? {}
    let sum = 0
    Object.keys(groupData).forEach((id) => {
      if (id === 'all') return
      if (include && !include(id)) return
      const value = flowValue(groupData[id], mode)
      sum += value
      if (!instancePoints.has(id)) instancePoints.set(id, [])
      instancePoints.get(id)?.push({ timestamp, power: value })
    })
    all.push({ timestamp, power: include ? sum : flowValue(groupData.all, mode) })
  })

  const timestamps = entryTimestamps(entries)
  const individual: InstanceSeries[] = Array.from(instancePoints.entries()).map(([id, points]) => ({
    id,
    label: names[id] ?? `${fallbackLabel} ${id.replace(/\D/g, '')}`,
    points: alignSeries(points, timestamps),
  }))
  return { all, individual }
}

function buildCombinedOnly(points: InstancePoint[]): CategoryData {
  return { all: points, individual: [] }
}

function buildHouseCategory(
  entries: DailyLogEntry[],
  names: Record<string, string>,
  isPart: (group: 'consumer' | 'counter', id: string) => boolean,
): CategoryData {
  const all: InstancePoint[] = []
  const rest: InstancePoint[] = []
  const parts = new Map<string, InstancePoint[]>()

  entries.forEach((entry) => {
    const timestamp = entry.timestamp * 1000
    const total = flowValue(entry.hc?.all, 'import')
    let partsSum = 0
    const add = (id: string, value: number) => {
      partsSum += value
      if (!parts.has(id)) parts.set(id, [])
      parts.get(id)?.push({ timestamp, power: value })
    }
    Object.entries(entry.consumer ?? {}).forEach(([id, flow]) => {
      if (id !== 'all' && isPart('consumer', id)) add(id, flowValue(flow, 'import'))
    })
    Object.entries(entry.counter ?? {}).forEach(([id, flow]) => {
      if (!flow.grid && isPart('counter', id)) add(id, flowValue(flow, 'net'))
    })
    all.push({ timestamp, power: total })
    rest.push({ timestamp, power: total - partsSum })
  })

  if (parts.size === 0) return { all, individual: [] }
  const individual: InstanceSeries[] = [
    { id: 'rest', label: 'Haus (übrig)', points: rest },
    ...Array.from(parts.entries()).map(([id, points]) => ({
      id,
      label: names[id] ?? `${id.startsWith('counter') ? 'Zähler' : 'Verbraucher'} ${id.replace(/\D/g, '')}`,
      points: alignSeries(points, all.map((p) => p.timestamp)),
    })),
  ]
  return { all, individual }
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

/** Sub-meters have no 'all' key in the log, so the sum is built here, without the grid counter. */
function buildCounterCategory(
  entries: DailyLogEntry[],
  names: Record<string, string>,
  include: (id: string) => boolean,
): CategoryData {
  const all: InstancePoint[] = []
  const instancePoints = new Map<string, InstancePoint[]>()

  entries.forEach((entry) => {
    const timestamp = entry.timestamp * 1000
    let sum = 0
    Object.entries(entry.counter ?? {}).forEach(([id, flow]) => {
      if (flow.grid || !include(id)) return
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
    points: alignSeries(points, entryTimestamps(entries)),
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

function buildForecast(entries: DailyLogEntry[]): InstancePoint[] {
  return entries
    .filter((entry): entry is DailyLogEntry & { forecast: number } => typeof entry.forecast === 'number')
    .map((entry) => ({ timestamp: entry.timestamp * 1000, power: entry.forecast / 1000 }))
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

/** Log entries are written every 5 minutes; every request recomputes the whole day in the backend's single command thread and is answered to every open tab. */
export const DAILY_LOG_REFRESH_MS = 5 * 60_000
const DAILY_LOG_CHECK_MS = 30_000

export function dailyLogRefreshDue(state: { followToday: boolean; hidden: boolean; lastFetchAt: number; now: number }): boolean {
  return state.followToday && !state.hidden && state.now - state.lastFetchAt >= DAILY_LOG_REFRESH_MS
}

/** Day log as chart series. Follows today (also across midnight) until the user navigates to a past day. */
export function useDailyLog(enabled: Ref<boolean> = ref(true)) {
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
  function goToDate(date: Date): void {
    const d = startOfDay(date)
    const today = startOfDay(new Date())
    if (d.getTime() >= today.getTime()) {
      goToToday()
    } else {
      followToday.value = false
      selectedDate.value = d
    }
  }

  const log = computed(() => mqttStore.getValue<DailyLogResponse | undefined>(topic.value, undefined))
  const entries = computed(() => log.value?.entries ?? [])
  const names = computed(() => log.value?.names ?? {})

  function isHomeConsumption(group: 'consumer' | 'counter', id: string): boolean {
    const num = instanceNumber(id)
    return group === 'consumer' ? mqttStore.consumerInstanceIsHomeConsumption(num) : mqttStore.counterInstanceIsHomeConsumption(num)
  }

  const categories = computed<Record<CategoryKey, CategoryData>>(() => ({
    pv: buildCategory(entries.value, 'pv', 'export', names.value, 'Wechselrichter'),
    battery: buildCategory(entries.value, 'bat', 'net', names.value, 'Speicher'),
    chargepoint: buildCategory(entries.value, 'cp', 'import', names.value, 'Ladepunkt'),
    consumer: buildCategory(entries.value, 'consumer', 'import', names.value, 'Verbraucher', (id) => !isHomeConsumption('consumer', id)),
    grid: buildCombinedOnly(entries.value.map((e) => ({ timestamp: e.timestamp * 1000, power: gridPower(e) }))),
    house: buildHouseCategory(
      entries.value,
      names.value,
      (group, id) =>
        group === 'consumer' ? isHomeConsumption(group, id) : mqttStore.counterInstanceIsHouseSplitPart(instanceNumber(id)),
    ),
    counter: buildCounterCategory(entries.value, names.value, (id) => !isHomeConsumption('counter', id)),
  }))

  const batterySoc = computed<SocCategoryData>(() => buildBatterySoc(entries.value, names.value))
  const vehicleSocAll = computed<SocSeries[]>(() => buildVehicleSoc(entries.value, names.value))
  const forecast = computed<InstancePoint[]>(() => buildForecast(entries.value))

  // get_daily_log always answers (empty for a day without a log), so undefined means the response is not in yet
  const isLoading = computed(() => log.value === undefined)

  // follows the date (navigation, midnight): swap the subscription and request the new day
  let lastFetchAt = 0
  // a refused command would show an error for something the user never did
  function fetchLog(): void {
    if (!enabled.value) return
    lastFetchAt = Date.now()
    mqttStore.fetchDailyLog(selectedDate.value)
  }

  watch(enabled, (on) => {
    if (on) fetchLog()
  })

  watch(
    topic,
    (newTopic, oldTopic) => {
      if (oldTopic) mqttStore.unsubscribe(oldTopic)
      mqttStore.subscribe(newTopic)
      fetchLog()
    },
    { immediate: true },
  )

  // the backend only republishes on getDailyLog, so today's chart needs a re-fetch (it also carries selectedDate across midnight); past days never change; a background tab catches up when visible
  let checkTimer: ReturnType<typeof setInterval> | undefined

  function refreshIfDue(): void {
    const hidden = document.visibilityState === 'hidden'
    if (!followToday.value || hidden) return
    const today = startOfDay(new Date())
    if (today.getTime() !== selectedDate.value.getTime()) {
      selectedDate.value = today // the topic watcher fetches the new day
      return
    }
    if (dailyLogRefreshDue({ followToday: followToday.value, hidden, lastFetchAt, now: Date.now() })) fetchLog()
  }

  onMounted(() => {
    checkTimer = setInterval(refreshIfDue, DAILY_LOG_CHECK_MS)
    document.addEventListener('visibilitychange', refreshIfDue)
  })
  onUnmounted(() => {
    mqttStore.unsubscribe(topic.value)
    clearInterval(checkTimer)
    document.removeEventListener('visibilitychange', refreshIfDue)
  })

  return {
    categories,
    isLoading,
    batterySoc,
    vehicleSocAll,
    forecast,
    selectedDate,
    isToday,
    goToPreviousDay,
    goToNextDay,
    goToToday,
    goToDate,
  }
}
