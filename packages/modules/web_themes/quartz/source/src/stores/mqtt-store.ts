import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import mqtt, { type MqttClient } from 'mqtt'
import type { QoS } from 'mqtt-packet'

type TopicMap = Record<string, unknown>
type SubscriptionCounts = Record<string, number>

/** openWB/graph/lastlivevaluesJson - all power fields are already in kW (see helpermodules/graph.py). */
export interface LiveValues {
  timestamp: number
  grid: number
  'house-power': number
  'charging-all': number
  'consumer-all': number
  'pv-all': number
  'bat-all-power'?: number
  'bat-all-soc'?: number
}

/**
 * openWB/graph/alllivevaluesJson* chunks carry the same data_line shape as lastlivevaluesJson
 * (see helpermodules/graph.py::pub_graph_data), including per-instance fields like 'cp2-power',
 * 'counter3-power', 'consumer11-power' - no fixed instance count, hence the index signature.
 */
export interface RawLivePoint {
  timestamp: number
  grid?: number
  'house-power'?: number
  'charging-all'?: number
  'consumer-all'?: number
  'pv-all'?: number
  'bat-all-power'?: number
  [key: string]: number | undefined
}

export interface ChargePointConnectedVehicleInfo {
  id: number
  name: string
}
export interface ChargePointConnectedVehicleSoc {
  soc?: number
  range?: number
  range_charged: number
  range_unit: string
  fault_state: number
  fault_str: string
}

/** A charge_template's chargemode.<mode>.limit - caps a mode by target SoC or energy amount. */
export interface Limit {
  selected: 'none' | 'soc' | 'amount'
  soc: number
  amount: number
}

/** See helpermodules/abstract_plans.py::ScheduledLimit - Zielladen's own differently-shaped limit. */
export interface ScheduledLimit {
  selected: 'soc' | 'amount'
  amount: number
  soc_limit: number
  soc_scheduled: number
}

/** A recurrence rule shared by both plan types, differing only in what 'once' holds. */
export interface FrequencyDate {
  selected: 'daily' | 'weekly' | 'once'
  once: string
  weekly: boolean[]
}
export interface FrequencyPeriod {
  selected: 'daily' | 'weekly' | 'once'
  once: [string, string]
  weekly: boolean[]
}

/** A Zielladen (target-charging) appointment - see abstract_plans.py::ScheduledChargingPlan. */
export interface ScheduledChargingPlan {
  active: boolean
  time: string
  frequency: FrequencyDate
  current: number
  dc_current: number
  id: number | null
  name: string
  limit: ScheduledLimit
  phases_to_use: number
  phases_to_use_pv: number
  bidi_charging_enabled: boolean
  bidi_power: number
  et_active: boolean
}

/** A Zeitladen (time-window charging) plan - see abstract_plans.py::TimeChargingPlan. */
export interface TimeChargingPlan {
  active: boolean
  time: [string, string]
  frequency: FrequencyPeriod
  current: number
  dc_current: number
  id: number | null
  limit: Limit
  min_bat_soc: number | null
  name: string
  phases_to_use: number
}

/** The full charge_template of whichever vehicle is connected to a chargepoint - see control/ev/charge_template.py. */
export interface ChargeTemplate {
  id: number
  name: string
  load_default: boolean
  time_charging: { active: boolean; plans: TimeChargingPlan[] }
  chargemode: {
    selected: string
    instant_charging: { current: number; dc_current: number; phases_to_use: number; limit: Limit }
    pv_charging: {
      min_current: number
      dc_min_current: number
      min_soc: number
      min_soc_current: number
      dc_min_soc_current: number
      phases_to_use: number
      phases_to_use_min_soc: number
      limit: Limit
    }
    eco_charging: { current: number; dc_current: number; max_price: number; phases_to_use: number; limit: Limit }
    scheduled_charging: { plans: ScheduledChargingPlan[] }
  }
}

export interface VehicleListEntry {
  id: number
  name: string
}

/** One of the two components a variable electricity price can be made of - either may be unconfigured. */
export interface TariffProvider {
  name: string
  type: string
}

export const useMqttStore = defineStore('mqtt', () => {
  let client: MqttClient | null = null
  const clientId = Math.random().toString(36).replace(/[^a-z]+/g, '').substring(0, 6)

  const topics = ref<TopicMap>({})
  const subscriptions = ref<SubscriptionCounts>({})
  const connected = ref(false)

  function initialize(): void {
    const protocol = location.protocol === 'https:' ? 'wss' : 'ws'
    const port = parseInt(location.port) || (location.protocol === 'https:' ? 443 : 80)
    const connectUrl = `${protocol}://${location.hostname}:${port}/ws`
    client = mqtt.connect(connectUrl, {
      connectTimeout: 4000,
      reconnectPeriod: 4000,
      clean: false,
      clientId,
    })
    client.on('connect', () => {
      connected.value = true
      Object.keys(subscriptions.value).forEach((topic) => client?.subscribe(topic, { qos: 0 }))
    })
    client.on('close', () => {
      connected.value = false
    })
    client.on('offline', () => {
      connected.value = false
    })
    client.on('error', (error) => {
      console.error('MQTT error', error)
    })
    client.on('message', (topic, payload) => {
      if (payload.length === 0) {
        delete topics.value[topic]
        return
      }
      try {
        topics.value[topic] = JSON.parse(payload.toString())
      } catch {
        topics.value[topic] = payload.toString()
      }
    })
  }

  /** Subscribe to a topic, ref-counted so multiple consumers can share one subscription. */
  function subscribe(topic: string): void {
    const count = (subscriptions.value[topic] ?? 0) + 1
    subscriptions.value[topic] = count
    if (count === 1) {
      client?.subscribe(topic, { qos: 0 })
    }
  }

  function unsubscribe(topic: string): void {
    const count = (subscriptions.value[topic] ?? 0) - 1
    if (count <= 0) {
      delete subscriptions.value[topic]
      client?.unsubscribe(topic)
    } else {
      subscriptions.value[topic] = count
    }
  }

  /** Read a topic's current value, subscribing to it automatically on first access. */
  const getValue = computed(() => {
    return <T,>(topic: string, defaultValue: T): T => {
      if (!(topic in subscriptions.value)) {
        subscribe(topic)
      }
      const value = topics.value[topic]
      return value === undefined ? defaultValue : (value as T)
    }
  })

  /** All currently-known topics whose name starts with the given prefix. */
  function getWildcardValues(prefix: string): TopicMap {
    const result: TopicMap = {}
    for (const topic in topics.value) {
      if (topic.startsWith(prefix)) result[topic] = topics.value[topic]
    }
    return result
  }

  function doPublish(topic: string, payload: unknown, retain = true, qos: QoS = 0): void {
    client?.publish(topic, JSON.stringify(payload), { qos, retain })
  }

  /**
   * Patch one field (or the whole value) of an already-subscribed topic and optionally publish
   * the updated value back to its writable 'openWB/set/...' counterpart. Several backend config
   * objects (e.g. a chargepoint's charge_template) are edited this way: read the current full
   * object, patch one nested field, republish the whole object - there's no per-field topic.
   */
  function updateTopic(topic: string, payload: unknown, objectPath?: string, publish = false): void {
    if (!(topic in topics.value)) {
      console.warn('updateTopic: topic not subscribed yet', topic)
      return
    }
    if (objectPath !== undefined) {
      const keys = objectPath.split('.')
      let target = topics.value[topic] as Record<string, unknown>
      keys.forEach((key, index) => {
        if (index === keys.length - 1) target[key] = payload
        else target = target[key] as Record<string, unknown>
      })
    } else {
      topics.value[topic] = payload
    }
    if (publish) {
      doPublish(topic.replace('openWB/', 'openWB/set/'), topics.value[topic])
    }
  }

  /** Dispatch a backend command (e.g. getDailyLog) via the command/<clientId>/todo channel. */
  function sendCommand(command: string, data: Record<string, unknown> = {}): void {
    doPublish(`openWB/set/command/${clientId}/todo`, { command, data }, false)
  }

  // --- status strip ---

  const liveValues = computed(() => getValue.value<Partial<LiveValues>>('openWB/graph/lastlivevaluesJson', {}))
  const pvPower = computed(() => liveValues.value['pv-all'] ?? 0)
  const gridPower = computed(() => liveValues.value.grid ?? 0)
  const houseConsumption = computed(() => liveValues.value['house-power'] ?? 0)
  const consumerPower = computed(() => liveValues.value['consumer-all'] ?? 0)
  const chargePointSumPower = computed(() => liveValues.value['charging-all'] ?? 0)
  const batteryPower = computed(() => liveValues.value['bat-all-power'] ?? 0)
  const batterySoc = computed(() => liveValues.value['bat-all-soc'] ?? 0)

  const electricityPriceConfigured = computed(() => getValue.value<boolean>('openWB/optional/ep/configured', false))
  const electricityPrices = computed(() => getValue.value<Record<string, number>>('openWB/optional/ep/get/prices', {}))
  // prices are pruned server-side to "now or later" (see ElectricityPricingCard.vue), so the first entry is current
  const currentElectricityPrice = computed<number | undefined>(() => {
    const entries = Object.values(electricityPrices.value)
    return entries.length > 0 ? entries[0] * 100000 : undefined
  })

  // the two components a variable electricity price can be made of - either may be unconfigured
  function flexibleTariffPrices(): Record<string, number> {
    return getValue.value<Record<string, number>>('openWB/optional/ep/flexible_tariff/get/prices', {})
  }
  function gridFeePrices(): Record<string, number> {
    return getValue.value<Record<string, number>>('openWB/optional/ep/grid_fee/get/prices', {})
  }
  function flexibleTariffProvider(): TariffProvider | undefined {
    return getValue.value<TariffProvider | undefined>('openWB/optional/ep/flexible_tariff/provider', undefined)
  }
  function gridFeeProvider(): TariffProvider | undefined {
    return getValue.value<TariffProvider | undefined>('openWB/optional/ep/grid_fee/provider', undefined)
  }
  function flexibleTariffFaultState(): number {
    return getValue.value<number>('openWB/optional/ep/flexible_tariff/get/fault_state', 0)
  }
  function flexibleTariffFaultMessage(): string {
    return getValue.value<string>('openWB/optional/ep/flexible_tariff/get/fault_str', '')
  }
  function gridFeeFaultState(): number {
    return getValue.value<number>('openWB/optional/ep/grid_fee/get/fault_state', 0)
  }
  function gridFeeFaultMessage(): string {
    return getValue.value<string>('openWB/optional/ep/grid_fee/get/fault_str', '')
  }

  const forecastConfigured = computed(() => getValue.value<boolean>('openWB/optional/forecast/configured', false))
  function forecastProvider(): TariffProvider | undefined {
    return getValue.value<TariffProvider | undefined>('openWB/optional/forecast/provider', undefined)
  }
  function forecastFaultState(): number {
    return getValue.value<number>('openWB/optional/forecast/get/fault_state', 0)
  }
  function forecastFaultMessage(): string {
    return getValue.value<string>('openWB/optional/forecast/get/fault_str', '')
  }
  const forecastValues = computed(() => getValue.value<Record<string, number>>('openWB/optional/forecast/get/values', {}))
  // forecast values are NOT pruned server-side (unlike prices), so the series includes already-past slots too
  const forecastSeries = computed(() =>
    Object.entries(forecastValues.value)
      .map(([timestamp, wh]) => ({ timestamp: Number(timestamp) * 1000, power: wh / 1000 }))
      .sort((a, b) => a.timestamp - b.timestamp),
  )
  const currentForecastPower = computed<number | undefined>(() => {
    const entries = forecastSeries.value
    if (entries.length === 0) return undefined
    const now = Date.now()
    return ([...entries].reverse().find((entry) => entry.timestamp <= now) ?? entries[0]).power
  })

  // --- live view (recent rolling window, finer-grained than the 5-min daily log) ---

  // openWB/graph/alllivevaluesJson(1-16): chunked by runs/graphing.sh, each payload is newline-separated
  // JSON lines (not one JSON document) rather than a single value, so getValue()'s auto-JSON-parsing
  // leaves it as a raw string here - split/parse it the same way koala's mqtt-store does.
  const liveSeriesRaw = computed<RawLivePoint[]>(() => {
    const chunks = getWildcardValues('openWB/graph/alllivevaluesJson')
    const points: RawLivePoint[] = []
    Object.values(chunks).forEach((payload) => {
      if (typeof payload !== 'string') return
      payload.split('\n').forEach((line) => {
        if (line.startsWith('{') && line.endsWith('}')) {
          try {
            points.push(JSON.parse(line) as RawLivePoint)
          } catch {
            // malformed/partial line, skip it
          }
        }
      })
    })
    return points.sort((a, b) => a.timestamp - b.timestamp)
  })

  function subscribeLiveSeries(): void {
    subscribe('openWB/graph/+')
  }
  function unsubscribeLiveSeries(): void {
    unsubscribe('openWB/graph/+')
  }

  // --- chargepoints ---

  interface Hierarchy {
    id: number
    type: string
    children: Hierarchy[]
  }

  /** All component ids of a given type (e.g. 'cp') from the system-wide component tree. */
  function getObjectIds(type: string): number[] {
    const hierarchy = getValue.value<Hierarchy[]>('openWB/counter/get/hierarchy', [])
    const result: number[] = []
    const walk = (nodes: Hierarchy[]) => {
      nodes.forEach((node) => {
        if (node.type === type) result.push(node.id)
        walk(node.children)
      })
    }
    walk(hierarchy)
    return result
  }

  function subscribeChargePointList(): void {
    subscribe('openWB/counter/get/hierarchy')
  }
  function unsubscribeChargePointList(): void {
    unsubscribe('openWB/counter/get/hierarchy')
  }

  const chargePointIds = computed(() => getObjectIds('cp'))

  function chargePointConfig(id: number): Record<string, unknown> {
    return getValue.value<Record<string, unknown>>(`openWB/chargepoint/${id}/config`, {})
  }
  function chargePointName(id: number): string {
    return (chargePointConfig(id).name as string | undefined) ?? `Ladepunkt ${id}`
  }

  function chargePointPlugState(id: number): boolean {
    return getValue.value<boolean>(`openWB/chargepoint/${id}/get/plug_state`, false)
  }
  function chargePointChargeState(id: number): boolean {
    return getValue.value<boolean>(`openWB/chargepoint/${id}/get/charge_state`, false)
  }
  /** Current charging power in kW (the raw topic is in W). */
  function chargePointPower(id: number): number {
    return getValue.value<number>(`openWB/chargepoint/${id}/get/power`, 0) / 1000
  }
  /** Energy charged during the current plug-in session, in kWh (the raw field is in Wh). */
  function chargePointEnergyChargedPlugged(id: number): number {
    const log = getValue.value<Record<string, unknown>>(`openWB/chargepoint/${id}/set/log`, {})
    return ((log.imported_since_plugged as number | undefined) ?? 0) / 1000
  }
  function chargePointPhasesInUse(id: number): number {
    return getValue.value<number>(`openWB/chargepoint/${id}/get/phases_in_use`, 0)
  }
  function chargePointChargingCurrent(id: number): number {
    return getValue.value<number>(`openWB/chargepoint/${id}/set/current`, 0)
  }
  function chargePointStateMessage(id: number): string {
    return getValue.value<string>(`openWB/chargepoint/${id}/get/state_str`, '')
  }
  function chargePointFaultState(id: number): number {
    return getValue.value<number>(`openWB/chargepoint/${id}/get/fault_state`, 0)
  }
  function chargePointFaultMessage(id: number): string {
    return getValue.value<string>(`openWB/chargepoint/${id}/get/fault_str`, '')
  }

  function chargePointManualLock(id: number): boolean {
    return getValue.value<boolean>(`openWB/chargepoint/${id}/set/manual_lock`, false)
  }
  function setChargePointManualLock(id: number, locked: boolean): void {
    updateTopic(`openWB/chargepoint/${id}/set/manual_lock`, locked, undefined, true)
  }

  function chargePointConnectedVehicleInfo(id: number): ChargePointConnectedVehicleInfo | undefined {
    return getValue.value<ChargePointConnectedVehicleInfo | undefined>(
      `openWB/chargepoint/${id}/get/connected_vehicle/info`,
      undefined,
    )
  }
  function setChargePointConnectedVehicle(id: number, vehicleId: number, vehicleName: string): void {
    // optimistic local update (the backend relay takes a moment), then tell it which vehicle to assign
    updateTopic(`openWB/chargepoint/${id}/get/connected_vehicle/info`, { id: vehicleId, name: vehicleName })
    doPublish(`openWB/set/chargepoint/${id}/config/ev`, vehicleId)
  }
  function chargePointConnectedVehicleSoc(id: number): ChargePointConnectedVehicleSoc | undefined {
    return getValue.value<ChargePointConnectedVehicleSoc | undefined>(
      `openWB/chargepoint/${id}/get/connected_vehicle/soc`,
      undefined,
    )
  }

  /** The full charge_template of the vehicle currently connected to this chargepoint - read AND write target. */
  function chargePointChargeTemplate(id: number): ChargeTemplate | undefined {
    return getValue.value<ChargeTemplate | undefined>(`openWB/chargepoint/${id}/set/charge_template`, undefined)
  }
  function chargePointChargeMode(id: number): string | undefined {
    return chargePointChargeTemplate(id)?.chargemode.selected
  }
  function setChargePointChargeMode(id: number, mode: string): void {
    updateTopic(`openWB/chargepoint/${id}/set/charge_template`, mode, 'chargemode.selected', true)
  }
  /** Patch one dot-path field of the connected vehicle's charge_template, e.g. 'chargemode.instant_charging.current'. */
  function setChargePointChargeTemplateField(id: number, path: string, value: unknown): void {
    updateTopic(`openWB/chargepoint/${id}/set/charge_template`, value, path, true)
  }

  // --- vehicles ---

  function subscribeVehicleList(): void {
    subscribe('openWB/vehicle/+/name')
  }
  function unsubscribeVehicleList(): void {
    unsubscribe('openWB/vehicle/+/name')
  }

  const vehicleList = computed<VehicleListEntry[]>(() =>
    Object.entries(getWildcardValues('openWB/vehicle/'))
      .filter(([topic]) => topic.endsWith('/name'))
      .map(([topic, name]) => ({ id: Number(topic.split('/')[2]), name: name as string }))
      .sort((a, b) => a.id - b.id),
  )

  /** The vehicle's current SoC override value - works regardless of which soc_module is configured. */
  function vehicleManualSoc(vehicleId: number): number {
    const state = getValue.value<Record<string, unknown>>(`openWB/vehicle/${vehicleId}/soc_module/calculated_soc_state`, {})
    return (state.manual_soc as number | undefined) ?? (state.soc_start as number | undefined) ?? 0
  }
  function setVehicleManualSoc(vehicleId: number, chargePointId: number, value: number): void {
    doPublish(`openWB/set/vehicle/${vehicleId}/soc_module/calculated_soc_state/manual_soc`, value)
    // also nudge the chargepoint's own displayed soc so the UI doesn't wait for the backend round-trip
    const cpTopic = `openWB/chargepoint/${chargePointId}/get/connected_vehicle/soc`
    if ((getValue.value<{ soc?: number }>(cpTopic, {})).soc !== undefined) {
      updateTopic(cpTopic, value, 'soc')
    }
  }
  function vehicleForceSocUpdate(vehicleId: number): void {
    doPublish(`openWB/set/vehicle/${vehicleId}/get/force_soc_update`, 1, false)
  }

  // --- daily log (chart history) ---

  function fetchDailyLog(date: Date = new Date()): void {
    const dateString =
      date.getFullYear().toString() +
      (date.getMonth() + 1).toString().padStart(2, '0') +
      date.getDate().toString().padStart(2, '0')
    subscribe(`openWB/log/daily/${dateString}`)
    sendCommand('getDailyLog', { date: dateString })
  }

  return {
    topics,
    subscriptions,
    connected,
    initialize,
    subscribe,
    unsubscribe,
    getValue,
    doPublish,
    sendCommand,
    pvPower,
    gridPower,
    houseConsumption,
    consumerPower,
    chargePointSumPower,
    batteryPower,
    batterySoc,
    electricityPriceConfigured,
    electricityPrices,
    currentElectricityPrice,
    flexibleTariffPrices,
    gridFeePrices,
    flexibleTariffProvider,
    gridFeeProvider,
    flexibleTariffFaultState,
    flexibleTariffFaultMessage,
    gridFeeFaultState,
    gridFeeFaultMessage,
    forecastConfigured,
    forecastProvider,
    forecastFaultState,
    forecastFaultMessage,
    forecastSeries,
    currentForecastPower,
    fetchDailyLog,
    liveSeriesRaw,
    subscribeLiveSeries,
    unsubscribeLiveSeries,
    updateTopic,
    chargePointIds,
    subscribeChargePointList,
    unsubscribeChargePointList,
    chargePointName,
    chargePointPlugState,
    chargePointChargeState,
    chargePointPower,
    chargePointEnergyChargedPlugged,
    chargePointPhasesInUse,
    chargePointChargingCurrent,
    chargePointStateMessage,
    chargePointFaultState,
    chargePointFaultMessage,
    chargePointManualLock,
    setChargePointManualLock,
    chargePointConnectedVehicleInfo,
    setChargePointConnectedVehicle,
    chargePointConnectedVehicleSoc,
    chargePointChargeTemplate,
    chargePointChargeMode,
    setChargePointChargeMode,
    setChargePointChargeTemplateField,
    vehicleList,
    subscribeVehicleList,
    unsubscribeVehicleList,
    vehicleManualSoc,
    setVehicleManualSoc,
    vehicleForceSocUpdate,
  }
})
