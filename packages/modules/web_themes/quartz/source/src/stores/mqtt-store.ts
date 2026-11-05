import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import mqtt, { type MqttClient } from 'mqtt'
import type { QoS } from 'mqtt-packet'
import { eurPerWhToCtPerKwh, ctPerKwhToEurPerWh } from '@/utils/format'

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
/** openWB/consumer/<id>/usage - a consumer's entire controllable state is this one JSON topic. */
export interface ConsumerUsage {
  type: string
  chargemode: string
  reset_chargemode: {
    active: boolean
    chargemode: string
    time: string
    frequency: FrequencyDate
  }
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

export interface VehicleInfo {
  manufacturer?: string
  model?: string
}

/** One chargepoint a vehicle is currently connected to (koala derives this the same way - no direct topic). */
export interface VehicleConnectionState {
  id: number
  name: string
  plugged: boolean
  charging: boolean
}

/** One of the two components a variable electricity price can be made of - either may be unconfigured. */
export interface TariffProvider {
  name: string
  type: string
}

/** The generic per-component config every component type publishes - name/manufacturer/model/color. */
export interface ComponentConfiguration {
  name: string
  info?: { manufacturer?: string; model?: string }
  color?: string
}

/** One entry of openWB/counter/get/loadmanagement_prios - see control/counter_all/loadmanagement_prio.py. */
interface LoadmanagementPrioEntry {
  type: string
  id?: number
  children?: LoadmanagementPrioEntry[]
}

/**
 * Shared mutual-clamp shape for a two-handle min/max range (battery priority SoC, active
 * battery control SoC) - whichever side the caller just moved wins and pushes the other side
 * along with it instead of letting the range invert (min > max). The caller always passes both
 * values (the one just dragged plus the other's last known value), so comparing each against
 * the currently stored value identifies which one changed.
 */
function clampMinMaxRange(newMin: number, newMax: number, oldMin: number, oldMax: number): [number, number] {
  if (newMin !== oldMin) return [newMin, Math.max(newMin, newMax)]
  if (newMax !== oldMax) return [Math.min(newMin, newMax), newMax]
  return [newMin, newMax]
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
    return entries.length > 0 ? eurPerWhToCtPerKwh(entries[0]) : undefined
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

  // --- access control (user management) ---
  // Published per logged-in session by the backend's own auth system - a user with restricted
  // access simply never receives 'true' for a section they're not allowed to see. Same topics and
  // shape koala's own mqtt-store.ts already reads; Quartz mirrors it rather than inventing its own.

  function accessAllowed(): boolean {
    return getValue.value<boolean>('openWB/system/security/access_allowed', false)
  }
  function accessSettingsAllowed(): boolean {
    return getValue.value<boolean>('openWB/system/security/access/Settings', false)
  }
  function accessStatusAllowed(): boolean {
    return getValue.value<boolean>('openWB/system/security/access/Status', false)
  }
  function accessChargeLogAllowed(): boolean {
    return getValue.value<boolean>('openWB/system/security/access/ChargeLog', false)
  }
  function accessChartAllowed(): boolean {
    return getValue.value<boolean>('openWB/system/security/access/Chart', false)
  }

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

  /** The single grid/EVU counter - by backend convention always the hierarchy's root node (see control/counter_all/counter_all.py::get_id_evu_counter). */
  function gridCounterId(): number | undefined {
    const hierarchy = getValue.value<Hierarchy[]>('openWB/counter/get/hierarchy', [])
    return hierarchy[0]?.type === 'counter' ? hierarchy[0].id : undefined
  }

  /** The component hierarchy backs every entity type's id list (chargepoints/consumers/counters/inverters/batteries), not just chargepoints. */
  function subscribeComponentHierarchy(): void {
    subscribe('openWB/counter/get/hierarchy')
  }
  function unsubscribeComponentHierarchy(): void {
    unsubscribe('openWB/counter/get/hierarchy')
  }

  const chargePointIds = computed(() => getObjectIds('cp'))
  const batteryIds = computed(() => getObjectIds('bat'))
  const inverterIds = computed(() => getObjectIds('inverter'))
  const consumerIds = computed(() => getObjectIds('consumer'))
  const counterIds = computed(() => getObjectIds('counter'))

  /** The device id isn't known client-side, hence the '+' - a real single-level MQTT wildcard, unlike
   *  getWildcardValues' plain string-prefix matching (which can't match this: the delivered topic has a
   *  real device id where this topic string still has the literal '+'). Matched locally via regex instead. */
  function getComponentConfiguration(id: number): ComponentConfiguration | undefined {
    const topic = `openWB/system/device/+/component/${id}/config`
    if (!(topic in subscriptions.value)) subscribe(topic)
    const pattern = new RegExp(`^${topic.replace(/\+/g, '[^/]+')}$`)
    for (const key in topics.value) {
      if (pattern.test(key)) return topics.value[key] as ComponentConfiguration
    }
    return undefined
  }

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
  /** Phase setpoint (distinct from chargePointPhasesInUse, which is the actually-active count). */
  function chargePointPhasesToUse(id: number): number {
    return getValue.value<number>(`openWB/chargepoint/${id}/set/phases_to_use`, 0)
  }
  function chargePointMaxEvseCurrent(id: number): number | undefined {
    return getValue.value<number | undefined>(`openWB/chargepoint/${id}/get/max_evse_current`, undefined)
  }
  function chargePointInstanceVoltages(id: number): number[] {
    return getValue.value<number[]>(`openWB/chargepoint/${id}/get/voltages`, [])
  }
  function chargePointInstanceCurrents(id: number): number[] {
    return getValue.value<number[]>(`openWB/chargepoint/${id}/get/currents`, [])
  }
  /** Per-phase power in kW (the raw topic is in W, same convention as chargePointPower). */
  function chargePointInstancePowers(id: number): number[] {
    return getValue.value<number[]>(`openWB/chargepoint/${id}/get/powers`, []).map((p) => p / 1000)
  }
  function chargePointInstancePowerFactors(id: number): number[] {
    return getValue.value<number[]>(`openWB/chargepoint/${id}/get/power_factors`, [])
  }
  function chargePointFrequency(id: number): number {
    return getValue.value<number>(`openWB/chargepoint/${id}/get/frequency`, 0)
  }
  /** Lifetime/daily imported-exported in kWh (raw topics are in Wh). */
  function chargePointInstanceDailyImported(id: number): number {
    return getValue.value<number>(`openWB/chargepoint/${id}/get/daily_imported`, 0) / 1000
  }
  function chargePointInstanceDailyExported(id: number): number {
    return getValue.value<number>(`openWB/chargepoint/${id}/get/daily_exported`, 0) / 1000
  }
  function chargePointInstanceImported(id: number): number {
    return getValue.value<number>(`openWB/chargepoint/${id}/get/imported`, 0) / 1000
  }
  function chargePointInstanceExported(id: number): number {
    return getValue.value<number>(`openWB/chargepoint/${id}/get/exported`, 0) / 1000
  }
  function chargePointFaultState(id: number): number {
    return getValue.value<number>(`openWB/chargepoint/${id}/get/fault_state`, 0)
  }
  function chargePointFaultMessage(id: number): string {
    return getValue.value<string>(`openWB/chargepoint/${id}/get/fault_str`, '')
  }
  function chargePointFaultStateTotal(): number {
    return getValue.value<number>('openWB/chargepoint/get/fault_state', 0)
  }
  function chargePointFaultMessageTotal(): string {
    return getValue.value<string>('openWB/chargepoint/get/fault_str', '')
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
  /** chargePointId is only needed to also nudge that chargepoint's own cached soc display (ChargePointCard's use case). */
  function setVehicleManualSoc(vehicleId: number, value: number, chargePointId?: number): void {
    doPublish(`openWB/set/vehicle/${vehicleId}/soc_module/calculated_soc_state/manual_soc`, value)
    const vehicleSocTopic = `openWB/vehicle/${vehicleId}/get/soc`
    if (getValue.value<number | undefined>(vehicleSocTopic, undefined) !== undefined) {
      updateTopic(vehicleSocTopic, value)
    }
    if (chargePointId === undefined) return
    const cpTopic = `openWB/chargepoint/${chargePointId}/get/connected_vehicle/soc`
    if ((getValue.value<{ soc?: number }>(cpTopic, {})).soc !== undefined) {
      updateTopic(cpTopic, value, 'soc')
    }
  }
  function vehicleForceSocUpdate(vehicleId: number): void {
    doPublish(`openWB/set/vehicle/${vehicleId}/get/force_soc_update`, 1, false)
  }
  /** True while a forced SoC update is pending - update_soc.py republishes this False once it's actually run the fetch. */
  function vehicleSocUpdateInProgress(vehicleId: number): boolean {
    return getValue.value<boolean>(`openWB/vehicle/${vehicleId}/get/force_soc_update`, false)
  }

  function vehicleInfo(id: number): VehicleInfo | undefined {
    return getValue.value<VehicleInfo | undefined>(`openWB/vehicle/${id}/info`, undefined)
  }
  function vehicleSocType(id: number): string | undefined {
    return getValue.value<{ type?: string } | undefined>(`openWB/vehicle/${id}/soc_module/config`, undefined)?.type
  }
  function vehicleColor(id: number): string | undefined {
    return getValue.value<string | undefined>(`openWB/vehicle/${id}/color`, undefined)
  }
  function vehicleSocValue(id: number): number | undefined {
    return getValue.value<number | undefined>(`openWB/vehicle/${id}/get/soc`, undefined)
  }
  function vehicleRange(id: number): number | undefined {
    return getValue.value<number | undefined>(`openWB/vehicle/${id}/get/range`, undefined)
  }
  /** Unix seconds of the last SoC request - when the SoC value itself was last updated. */
  function vehicleSocTimestamp(id: number): number | undefined {
    return getValue.value<number | undefined>(`openWB/vehicle/${id}/get/soc_timestamp`, undefined)
  }
  function vehicleOdometer(id: number): number | undefined {
    return getValue.value<number | undefined>(`openWB/vehicle/${id}/get/odometer`, undefined)
  }
  function vehicleFaultState(id: number): number {
    return getValue.value<number>(`openWB/vehicle/${id}/get/fault_state`, 0)
  }
  function vehicleFaultMessage(id: number): string {
    return getValue.value<string>(`openWB/vehicle/${id}/get/fault_str`, '')
  }

  function subscribeLoadmanagementPrios(): void {
    subscribe('openWB/counter/get/loadmanagement_prios')
  }
  function unsubscribeLoadmanagementPrios(): void {
    unsubscribe('openWB/counter/get/loadmanagement_prios')
  }

  /** 1-based rank in the load-management priority order (used by the real surplus-charging algorithm to
   *  decide charging order) - a 'group' entry's children all share that group's rank, same as the colors
   *  theme's own assignPriority() derives it. Shared by vehicles and consumers, the only two entry types
   *  this list can contain (see control/counter_all/loadmanagement_prio.py). */
  function loadmanagementPriority(type: 'vehicle' | 'consumer', id: number): number | undefined {
    const entries = getValue.value<LoadmanagementPrioEntry[]>('openWB/counter/get/loadmanagement_prios', [])
    for (let i = 0; i < entries.length; i++) {
      const entry = entries[i]
      if (entry.type === type && entry.id === id) return i + 1
      if (entry.type === 'group' && entry.children?.some((child) => child.type === type && child.id === id)) {
        return i + 1
      }
    }
    return undefined
  }
  function vehiclePriority(vehicleId: number): number | undefined {
    return loadmanagementPriority('vehicle', vehicleId)
  }
  function consumerPriority(consumerId: number): number | undefined {
    return loadmanagementPriority('consumer', consumerId)
  }

  /** At most 2 vehicles worth charting a SoC line for - connected-to-a-chargepoint ones first
   *  (most relevant right now), then any other vehicle with a real SoC reading, same priority
   *  order the 'colors' theme's own chart uses (chargePointList/model.ts::topVehicles). */
  const topVehicleIds = computed<number[]>(() => {
    const connected = chargePointIds.value
      .map((id) => chargePointConnectedVehicleInfo(id)?.id)
      .filter((id): id is number => id !== undefined && vehicleSocValue(id) !== undefined)
    const others = vehicleList.value
      .map((v) => v.id)
      .filter((id) => !connected.includes(id) && vehicleSocValue(id) !== undefined)
    return [...new Set([...connected, ...others])].slice(0, 2)
  })

  function subscribeVehicleConnectionState(): void {
    subscribe('openWB/chargepoint/+/get/connected_vehicle/info')
  }
  function unsubscribeVehicleConnectionState(): void {
    unsubscribe('openWB/chargepoint/+/get/connected_vehicle/info')
  }

  /** Every chargepoint this vehicle is currently connected to - no direct vehicle-side topic for this, derived the same way koala does it. */
  function vehicleConnectionState(vehicleId: number): VehicleConnectionState[] {
    const connected = getWildcardValues('openWB/chargepoint/')
    return Object.entries(connected)
      .filter(([topic]) => topic.endsWith('/get/connected_vehicle/info'))
      .filter(([, info]) => (info as ChargePointConnectedVehicleInfo | undefined)?.id === vehicleId)
      .map(([topic]) => {
        const id = Number(topic.split('/')[2])
        return {
          id,
          name: chargePointName(id),
          plugged: chargePointPlugState(id),
          charging: chargePointChargeState(id),
        }
      })
  }

  // --- batteries ---

  function batteryName(id: number): string {
    return getComponentConfiguration(id)?.name ?? `Speicher ${id}`
  }
  function batteryInstanceSoc(id: number): number | undefined {
    return getValue.value<number | undefined>(`openWB/bat/${id}/get/soc`, undefined)
  }
  /** Current power in kW (the raw topic is in W). */
  function batteryInstancePower(id: number): number {
    return getValue.value<number>(`openWB/bat/${id}/get/power`, 0) / 1000
  }
  /** Energy today in kWh (the raw topics are in Wh). */
  function batteryInstanceDailyImported(id: number): number {
    return getValue.value<number>(`openWB/bat/${id}/get/daily_imported`, 0) / 1000
  }
  function batteryInstanceDailyExported(id: number): number {
    return getValue.value<number>(`openWB/bat/${id}/get/daily_exported`, 0) / 1000
  }
  /** Lifetime energy in kWh (the raw topics are in Wh). */
  function batteryInstanceImported(id: number): number {
    return getValue.value<number>(`openWB/bat/${id}/get/imported`, 0) / 1000
  }
  function batteryInstanceExported(id: number): number {
    return getValue.value<number>(`openWB/bat/${id}/get/exported`, 0) / 1000
  }
  function batteryInstanceCurrents(id: number): number[] {
    return getValue.value<number[]>(`openWB/bat/${id}/get/currents`, [])
  }
  /** Status of an active battery-control mode (e.g. "Hält SoC bei X%") - empty when self-regulated. */
  function batteryInstanceStateMessage(id: number): string {
    return getValue.value<string>(`openWB/bat/${id}/get/state_str`, '')
  }
  function batteryInstanceFaultState(id: number): number {
    return getValue.value<number>(`openWB/bat/${id}/get/fault_state`, 0)
  }
  function batteryInstanceFaultMessage(id: number): string {
    return getValue.value<string>(`openWB/bat/${id}/get/fault_str`, '')
  }

  /** System-wide totals - power/soc reuse the existing graph-snapshot-sourced batteryPower/batterySoc above, these cover what that snapshot doesn't. */
  function batteryDailyImportedTotal(): number {
    return getValue.value<number>('openWB/bat/get/daily_imported', 0) / 1000
  }
  function batteryDailyExportedTotal(): number {
    return getValue.value<number>('openWB/bat/get/daily_exported', 0) / 1000
  }
  function batteryFaultStateTotal(): number {
    return getValue.value<number>('openWB/bat/get/fault_state', 0)
  }
  function batteryFaultMessageTotal(): string {
    return getValue.value<string>('openWB/bat/get/fault_str', '')
  }

  /** The global PV-surplus priority order (vehicles vs. battery vs. battery-SoC-gated) - not per-battery, same value regardless of which battery card edits it. */
  function batteryMode(): string {
    return getValue.value<string>('openWB/general/chargemode_config/bat/mode', 'ev_mode')
  }
  function setBatteryMode(mode: string): void {
    updateTopic('openWB/general/chargemode_config/bat/mode', mode, undefined, true)
  }
  function batteryPrioritySocMin(): number {
    return getValue.value<number>('openWB/general/chargemode_config/bat/min_soc', 0)
  }
  function batteryPrioritySocMax(): number {
    return getValue.value<number>('openWB/general/chargemode_config/bat/max_soc', 100)
  }
  function setBatteryPrioritySoc(min: number, max: number): void {
    const [clampedMin, clampedMax] = clampMinMaxRange(min, max, batteryPrioritySocMin(), batteryPrioritySocMax())
    updateTopic('openWB/general/chargemode_config/bat/min_soc', clampedMin, undefined, true)
    updateTopic('openWB/general/chargemode_config/bat/max_soc', clampedMax, undefined, true)
  }

  /** Whether to reserve some charging power for the battery below min-SoC instead of giving it all to vehicles/consumers. */
  function batteryPowerReserveActive(): boolean {
    return getValue.value<boolean>('openWB/general/chargemode_config/bat/power_reserve_active', false)
  }
  function setBatteryPowerReserveActive(active: boolean): void {
    updateTopic('openWB/general/chargemode_config/bat/power_reserve_active', active, undefined, true)
  }
  /** Reserved charging power in kW (the raw topic is in W). */
  function batteryPowerReserve(): number {
    return getValue.value<number>('openWB/general/chargemode_config/bat/power_reserve', 2000) / 1000
  }
  function setBatteryPowerReserve(kw: number): void {
    updateTopic('openWB/general/chargemode_config/bat/power_reserve', Math.round(kw * 1000), undefined, true)
  }

  /** Whether to allow the battery to discharge above max-SoC instead of holding its charge there. */
  function batteryPowerDischargeActive(): boolean {
    return getValue.value<boolean>('openWB/general/chargemode_config/bat/power_discharge_active', false)
  }
  function setBatteryPowerDischargeActive(active: boolean): void {
    updateTopic('openWB/general/chargemode_config/bat/power_discharge_active', active, undefined, true)
  }
  /** Allowed discharge power in kW (the raw topic is in W). */
  function batteryPowerDischarge(): number {
    return getValue.value<number>('openWB/general/chargemode_config/bat/power_discharge', 1500) / 1000
  }
  function setBatteryPowerDischarge(kw: number): void {
    updateTopic('openWB/general/chargemode_config/bat/power_discharge', Math.round(kw * 1000), undefined, true)
  }

  // --- active battery control (openwb-ui-settings' ActiveBatControlConfiguration.vue) ---

  /** Whether a battery's charge/discharge power can be overridden at all - undefined while not yet known (distinct from a confirmed false). */
  function batteryInstancePowerLimitControllable(id: number): boolean | undefined {
    return getValue.value<boolean | undefined>(`openWB/bat/${id}/get/power_limit_controllable`, undefined)
  }
  /** Max charge power in kW (the raw topic is in W). Only meaningful/editable for controllable batteries. */
  function batteryInstanceMaxChargePower(id: number): number {
    return getValue.value<number>(`openWB/bat/${id}/get/max_charge_power`, 0) / 1000
  }
  function setBatteryInstanceMaxChargePower(id: number, kw: number): void {
    updateTopic(`openWB/bat/${id}/get/max_charge_power`, Math.round(kw * 1000), undefined, true)
  }
  /** Max discharge power in kW - the raw topic is stored negative (W), display/input use a positive kW value. */
  function batteryInstanceMaxDischargePower(id: number): number {
    return getValue.value<number>(`openWB/bat/${id}/get/max_discharge_power`, 0) / -1000
  }
  function setBatteryInstanceMaxDischargePower(id: number, kw: number): void {
    updateTopic(`openWB/bat/${id}/get/max_discharge_power`, Math.round(kw * -1000), undefined, true)
  }

  // activation itself is a deliberate, liability-worded confirmation step done only in the
  // legacy settings UI - read-only here, no setter
  function batteryControlActivated(): boolean {
    return getValue.value<boolean>('openWB/bat/config/bat_control_activated', false)
  }
  function batteryControlMinSoc(): number {
    return getValue.value<number>('openWB/bat/config/bat_control_min_soc', 5)
  }
  function batteryControlMaxSoc(): number {
    return getValue.value<number>('openWB/bat/config/bat_control_max_soc', 90)
  }
  function setBatteryControlSocRange(min: number, max: number): void {
    const [clampedMin, clampedMax] = clampMinMaxRange(min, max, batteryControlMinSoc(), batteryControlMaxSoc())
    updateTopic('openWB/bat/config/bat_control_min_soc', clampedMin, undefined, true)
    updateTopic('openWB/bat/config/bat_control_max_soc', clampedMax, undefined, true)
  }

  function batteryPowerLimitCondition(): string {
    return getValue.value<string>('openWB/bat/config/power_limit_condition', 'manual')
  }
  /** Switching to 'vehicle_charging' forces manual_mode to 'manual_limit', matching the reference's own handlePowerLimitConditionChange. */
  function setBatteryPowerLimitCondition(condition: string): void {
    updateTopic('openWB/bat/config/power_limit_condition', condition, undefined, true)
    if (condition === 'vehicle_charging') {
      updateTopic('openWB/bat/config/manual_mode', 'manual_limit', undefined, true)
    }
  }
  function batteryManualMode(): string {
    return getValue.value<string>('openWB/bat/config/manual_mode', 'manual_limit')
  }
  function setBatteryManualMode(mode: string): void {
    updateTopic('openWB/bat/config/manual_mode', mode, undefined, true)
  }
  function batteryPowerLimitMode(): string {
    return getValue.value<string>('openWB/bat/config/power_limit_mode', 'mode_no_discharge')
  }
  function setBatteryPowerLimitMode(mode: string): void {
    updateTopic('openWB/bat/config/power_limit_mode', mode, undefined, true)
  }

  function batteryPriceLimitActivated(): boolean {
    return getValue.value<boolean>('openWB/bat/config/price_limit_activated', false)
  }
  function setBatteryPriceLimitActivated(active: boolean): void {
    updateTopic('openWB/bat/config/price_limit_activated', active, undefined, true)
  }
  function batteryPriceLimit(): number {
    return eurPerWhToCtPerKwh(getValue.value<number>('openWB/bat/config/price_limit', 0))
  }
  function setBatteryPriceLimit(ctPerKwh: number): void {
    updateTopic('openWB/bat/config/price_limit', ctPerKwhToEurPerWh(ctPerKwh), undefined, true)
  }
  function batteryPriceChargeActivated(): boolean {
    return getValue.value<boolean>('openWB/bat/config/price_charge_activated', false)
  }
  function setBatteryPriceChargeActivated(active: boolean): void {
    updateTopic('openWB/bat/config/price_charge_activated', active, undefined, true)
  }
  function batteryChargeLimit(): number {
    return eurPerWhToCtPerKwh(getValue.value<number>('openWB/bat/config/charge_limit', 0))
  }
  function setBatteryChargeLimit(ctPerKwh: number): void {
    updateTopic('openWB/bat/config/charge_limit', ctPerKwhToEurPerWh(ctPerKwh), undefined, true)
  }

  // --- counters ---

  function counterName(id: number): string {
    return getComponentConfiguration(id)?.name ?? `Zähler ${id}`
  }
  /** Current power in kW (the raw topic is in W). */
  function counterInstancePower(id: number): number {
    return getValue.value<number>(`openWB/counter/${id}/get/power`, 0) / 1000
  }
  /** Energy today in kWh (the raw topics are in Wh). */
  function counterInstanceDailyImported(id: number): number {
    return getValue.value<number>(`openWB/counter/${id}/get/daily_imported`, 0) / 1000
  }
  function counterInstanceDailyExported(id: number): number {
    return getValue.value<number>(`openWB/counter/${id}/get/daily_exported`, 0) / 1000
  }
  /** Lifetime energy in kWh (the raw topics are in Wh). */
  function counterInstanceImported(id: number): number {
    return getValue.value<number>(`openWB/counter/${id}/get/imported`, 0) / 1000
  }
  function counterInstanceExported(id: number): number {
    return getValue.value<number>(`openWB/counter/${id}/get/exported`, 0) / 1000
  }
  function counterInstanceFrequency(id: number): number {
    return getValue.value<number>(`openWB/counter/${id}/get/frequency`, 0)
  }
  function counterInstanceVoltages(id: number): number[] {
    return getValue.value<number[]>(`openWB/counter/${id}/get/voltages`, [])
  }
  function counterInstanceCurrents(id: number): number[] {
    return getValue.value<number[]>(`openWB/counter/${id}/get/currents`, [])
  }
  /** Per-phase power in kW (the raw topic is in W). */
  function counterInstancePowers(id: number): number[] {
    return getValue.value<number[]>(`openWB/counter/${id}/get/powers`, []).map((p) => p / 1000)
  }
  function counterInstancePowerFactors(id: number): number[] {
    return getValue.value<number[]>(`openWB/counter/${id}/get/power_factors`, [])
  }
  function counterInstanceFaultState(id: number): number {
    return getValue.value<number>(`openWB/counter/${id}/get/fault_state`, 0)
  }
  function counterInstanceFaultMessage(id: number): string {
    return getValue.value<string>(`openWB/counter/${id}/get/fault_str`, '')
  }

  // --- inverters (pv) ---

  function inverterName(id: number): string {
    return getComponentConfiguration(id)?.name ?? `Wechselrichter ${id}`
  }
  /** Current power in kW (the raw topic is in W). */
  function inverterInstancePower(id: number): number {
    return getValue.value<number>(`openWB/pv/${id}/get/power`, 0) / 1000
  }
  /** Energy exported today in kWh (the raw topic is in Wh) - PV only ever exports, no imported counterpart exists. */
  function inverterInstanceDailyExported(id: number): number {
    return getValue.value<number>(`openWB/pv/${id}/get/daily_exported`, 0) / 1000
  }
  function inverterInstanceMonthlyExported(id: number): number {
    return getValue.value<number>(`openWB/pv/${id}/get/monthly_exported`, 0) / 1000
  }
  function inverterInstanceYearlyExported(id: number): number {
    return getValue.value<number>(`openWB/pv/${id}/get/yearly_exported`, 0) / 1000
  }
  /** Lifetime energy exported in kWh (the raw topic is in Wh) - the inverter's "Zählerstand". */
  function inverterInstanceExported(id: number): number {
    return getValue.value<number>(`openWB/pv/${id}/get/exported`, 0) / 1000
  }
  function inverterInstanceCurrents(id: number): number[] {
    return getValue.value<number[]>(`openWB/pv/${id}/get/currents`, [])
  }
  function inverterInstanceFaultState(id: number): number {
    return getValue.value<number>(`openWB/pv/${id}/get/fault_state`, 0)
  }
  function inverterInstanceFaultMessage(id: number): string {
    return getValue.value<string>(`openWB/pv/${id}/get/fault_str`, '')
  }
  function pvFaultStateTotal(): number {
    return getValue.value<number>('openWB/pv/get/fault_state', 0)
  }
  function pvFaultMessageTotal(): string {
    return getValue.value<string>('openWB/pv/get/fault_str', '')
  }

  // --- consumers ---

  function consumerName(id: number): string {
    return getComponentConfiguration(id)?.name ?? `Verbraucher ${id}`
  }
  /** Current power in kW (the raw topic is in W). */
  function consumerInstancePower(id: number): number {
    return getValue.value<number>(`openWB/consumer/${id}/get/power`, 0) / 1000
  }
  /** Energy imported today in kWh (the raw topic is in Wh). */
  function consumerInstanceDailyImported(id: number): number {
    return getValue.value<number>(`openWB/consumer/${id}/get/daily_imported`, 0) / 1000
  }
  /** Not every consumer module publishes phase data - empty array when it doesn't. */
  function consumerInstanceVoltages(id: number): number[] {
    return getValue.value<number[]>(`openWB/consumer/${id}/get/voltages`, [])
  }
  function consumerInstanceCurrents(id: number): number[] {
    return getValue.value<number[]>(`openWB/consumer/${id}/get/currents`, [])
  }
  /** Per-phase power in kW (the raw topic is in W). */
  function consumerInstancePowers(id: number): number[] {
    return getValue.value<number[]>(`openWB/consumer/${id}/get/powers`, []).map((p) => p / 1000)
  }
  function consumerInstanceFaultState(id: number): number {
    return getValue.value<number>(`openWB/consumer/${id}/get/fault_state`, 0)
  }
  function consumerInstanceFaultMessage(id: number): string {
    return getValue.value<string>(`openWB/consumer/${id}/get/fault_str`, '')
  }
  function consumerFaultStateTotal(): number {
    return getValue.value<number>('openWB/consumer/get/fault_state', 0)
  }
  function consumerFaultMessageTotal(): string {
    return getValue.value<string>('openWB/consumer/get/fault_str', '')
  }
  function consumerInstanceStateMessage(id: number): string {
    return getValue.value<string>(`openWB/consumer/${id}/get/state_str`, '')
  }
  function consumerPlugState(id: number): boolean {
    return getValue.value<boolean>(`openWB/consumer/${id}/get/plug_state`, false)
  }
  function consumerChargeState(id: number): boolean {
    return getValue.value<boolean>(`openWB/consumer/${id}/get/charge_state`, false)
  }
  /** Runtime since the last reset, in seconds - a 'set/' topic despite being read-only from the UI's
   *  perspective, same convention as chargePointChargingCurrent's existing set/current read. */
  function consumerOnTime(id: number): number {
    return getValue.value<number>(`openWB/consumer/${id}/set/on_time`, 0)
  }
  /** Sensor readings in °C, if the configured module provides any (mostly heat-pump-ish modules). */
  function consumerTemperatures(id: number): number[] {
    return getValue.value<number[]>(`openWB/consumer/${id}/get/temperatures`, [])
  }

  function consumerUsage(id: number): ConsumerUsage | undefined {
    return getValue.value<ConsumerUsage | undefined>(`openWB/consumer/${id}/usage`, undefined)
  }
  function consumerUsageType(id: number): string | undefined {
    return consumerUsage(id)?.type
  }
  function consumerMode(id: number): string | undefined {
    return consumerUsage(id)?.chargemode
  }
  function setConsumerMode(id: number, mode: string): void {
    updateTopic(`openWB/consumer/${id}/usage`, mode, 'chargemode', true)
  }
  /** Patch one dot-path field of a consumer's reset_chargemode, e.g. 'frequency.selected'. */
  function setConsumerResetChargemodeField(id: number, path: string, value: unknown): void {
    updateTopic(`openWB/consumer/${id}/usage`, value, `reset_chargemode.${path}`, true)
  }

  // --- daily log (chart history) ---

  /** Only requests a fresh payload - subscribing to the (date-dependent) topic is the caller's responsibility, see useDailyLog.ts. */
  function fetchDailyLog(date: Date = new Date()): void {
    const dateString =
      date.getFullYear().toString() +
      (date.getMonth() + 1).toString().padStart(2, '0') +
      date.getDate().toString().padStart(2, '0')
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
    accessAllowed,
    accessSettingsAllowed,
    accessStatusAllowed,
    accessChargeLogAllowed,
    accessChartAllowed,
    fetchDailyLog,
    liveSeriesRaw,
    subscribeLiveSeries,
    unsubscribeLiveSeries,
    updateTopic,
    chargePointIds,
    subscribeComponentHierarchy,
    unsubscribeComponentHierarchy,
    chargePointName,
    chargePointPlugState,
    chargePointChargeState,
    chargePointPower,
    chargePointEnergyChargedPlugged,
    chargePointPhasesInUse,
    chargePointChargingCurrent,
    chargePointStateMessage,
    chargePointPhasesToUse,
    chargePointMaxEvseCurrent,
    chargePointInstanceVoltages,
    chargePointInstanceCurrents,
    chargePointInstancePowers,
    chargePointInstancePowerFactors,
    chargePointFrequency,
    chargePointInstanceDailyImported,
    chargePointInstanceDailyExported,
    chargePointInstanceImported,
    chargePointInstanceExported,
    chargePointFaultState,
    chargePointFaultMessage,
    chargePointFaultStateTotal,
    chargePointFaultMessageTotal,
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
    vehicleSocUpdateInProgress,
    vehicleInfo,
    vehicleSocType,
    vehicleColor,
    vehicleSocValue,
    vehicleRange,
    vehicleSocTimestamp,
    vehicleOdometer,
    vehicleFaultState,
    vehicleFaultMessage,
    subscribeVehicleConnectionState,
    unsubscribeVehicleConnectionState,
    vehicleConnectionState,
    subscribeLoadmanagementPrios,
    unsubscribeLoadmanagementPrios,
    vehiclePriority,
    consumerPriority,
    topVehicleIds,
    batteryIds,
    inverterIds,
    consumerIds,
    getComponentConfiguration,
    batteryName,
    batteryInstanceSoc,
    batteryInstancePower,
    batteryInstanceDailyImported,
    batteryInstanceDailyExported,
    batteryInstanceImported,
    batteryInstanceExported,
    batteryInstanceCurrents,
    batteryInstanceStateMessage,
    batteryInstanceFaultState,
    batteryInstanceFaultMessage,
    batteryDailyImportedTotal,
    batteryDailyExportedTotal,
    batteryFaultStateTotal,
    batteryFaultMessageTotal,
    batteryMode,
    setBatteryMode,
    batteryPrioritySocMin,
    batteryPrioritySocMax,
    setBatteryPrioritySoc,
    batteryPowerReserveActive,
    setBatteryPowerReserveActive,
    batteryPowerReserve,
    setBatteryPowerReserve,
    batteryPowerDischargeActive,
    setBatteryPowerDischargeActive,
    batteryPowerDischarge,
    setBatteryPowerDischarge,
    batteryInstancePowerLimitControllable,
    batteryInstanceMaxChargePower,
    setBatteryInstanceMaxChargePower,
    batteryInstanceMaxDischargePower,
    setBatteryInstanceMaxDischargePower,
    batteryControlActivated,
    batteryControlMinSoc,
    batteryControlMaxSoc,
    setBatteryControlSocRange,
    batteryPowerLimitCondition,
    setBatteryPowerLimitCondition,
    batteryManualMode,
    setBatteryManualMode,
    batteryPowerLimitMode,
    setBatteryPowerLimitMode,
    batteryPriceLimitActivated,
    setBatteryPriceLimitActivated,
    batteryPriceLimit,
    setBatteryPriceLimit,
    batteryPriceChargeActivated,
    setBatteryPriceChargeActivated,
    batteryChargeLimit,
    setBatteryChargeLimit,
    counterIds,
    gridCounterId,
    counterName,
    counterInstancePower,
    counterInstanceDailyImported,
    counterInstanceDailyExported,
    counterInstanceImported,
    counterInstanceExported,
    counterInstanceFrequency,
    counterInstanceVoltages,
    counterInstanceCurrents,
    counterInstancePowers,
    counterInstancePowerFactors,
    counterInstanceFaultState,
    counterInstanceFaultMessage,
    inverterName,
    inverterInstancePower,
    inverterInstanceDailyExported,
    inverterInstanceMonthlyExported,
    inverterInstanceYearlyExported,
    inverterInstanceExported,
    inverterInstanceCurrents,
    inverterInstanceFaultState,
    inverterInstanceFaultMessage,
    pvFaultStateTotal,
    pvFaultMessageTotal,
    consumerName,
    consumerInstancePower,
    consumerInstanceDailyImported,
    consumerInstanceVoltages,
    consumerInstanceCurrents,
    consumerInstancePowers,
    consumerInstanceFaultState,
    consumerInstanceFaultMessage,
    consumerFaultStateTotal,
    consumerFaultMessageTotal,
    consumerInstanceStateMessage,
    consumerPlugState,
    consumerChargeState,
    consumerOnTime,
    consumerTemperatures,
    consumerUsage,
    consumerUsageType,
    consumerMode,
    setConsumerMode,
    setConsumerResetChargemodeField,
  }
})
