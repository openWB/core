import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import mqtt, { type MqttClient } from 'mqtt'
import type { QoS } from 'mqtt-packet'
import { eurPerWhToCtPerKwh, ctPerKwhToEurPerWh, convertDcCurrentToPower } from '@/utils/format'
import { getCookie, setCookie, removeCookie } from '@/utils/cookies'
import { showErrorToast } from '@/composables/useToasts'

type TopicMap = Record<string, unknown>
type SubscriptionCounts = Record<string, number>

/** openWB/graph/lastlivevaluesJson; power fields are in kW. */
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

/** Chunk of openWB/graph/alllivevaluesJson*; per-instance fields like 'cp2-power' need the index signature. */
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
export interface ChargePointConnectedVehicleConfig {
  ev_template: number
}
export interface EvTemplate {
  bidi: boolean
}

export interface ChargePointConfig {
  name: string
  template: number
}
export interface ChargePointTemplate {
  charging_type: 'AC' | 'DC'
  dc_max_current: number
}

export interface Limit {
  selected: 'none' | 'soc' | 'amount'
  soc: number
  amount: number
}

export interface ScheduledLimit {
  selected: 'soc' | 'amount'
  amount: number
  soc_limit: number
  soc_scheduled: number
}

export interface FrequencyDate {
  selected: 'daily' | 'weekly' | 'once'
  once: string
  weekly: boolean[]
}
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

export interface VehicleConnectionState {
  id: number
  name: string
  plugged: boolean
  charging: boolean
}

export interface TariffProvider {
  name: string
  type: string
}

export interface ComponentConfiguration {
  name: string
  info?: { manufacturer?: string; model?: string }
  color?: string
}

interface LoadmanagementPrioEntry {
  type: string
  id?: number
  children?: LoadmanagementPrioEntry[]
}

/** Two-handle range: the handle that was just moved wins and pushes the other along, so min never exceeds max. */
function clampMinMaxRange(newMin: number, newMax: number, oldMin: number, oldMax: number): [number, number] {
  if (newMin !== oldMin) return [newMin, Math.max(newMin, newMax)]
  if (newMax !== oldMax) return [Math.min(newMin, newMax), newMax]
  return [newMin, newMax]
}

export const useMqttStore = defineStore('mqtt', () => {
  let client: MqttClient | null = null
  // part of the command topic, where the backend only accepts [A-Za-z0-9_]
  const clientId = `quartz_${Math.random().toString(36).slice(2).padEnd(8, '0').slice(0, 8)}`

  const topics = ref<TopicMap>({})
  const subscriptions = ref<SubscriptionCounts>({})
  const connected = ref(false)
  const authFailureMessage = ref('')
  const defaultCredentialsWarning = ref(false)

  /** The 'mqtt' cookie holds "username:password"; the broker validates it on CONNECT. */
  function mqttCredentials(): { username?: string; password?: string } {
    const raw = getCookie('mqtt')
    const match = raw?.match(/^([^:]+):(.+)$/)
    return match ? { username: match[1], password: match[2] } : {}
  }

  function initialize(): void {
    const protocol = location.protocol === 'https:' ? 'wss' : 'ws'
    const port = parseInt(location.port) || (location.protocol === 'https:' ? 443 : 80)
    const connectUrl = `${protocol}://${location.hostname}:${port}/ws`
    const { username, password } = mqttCredentials()
    // MQTT 5: only then does the broker report a refused publish (reason 135). Clean session: the client id is new on every load.
    client = mqtt.connect(connectUrl, {
      protocolVersion: 5,
      connectTimeout: 4000,
      reconnectPeriod: 4000,
      clientId,
      username,
      password,
    })
    client.on('connect', () => {
      connected.value = true
      Object.keys(subscriptions.value).forEach((topic) => client?.subscribe(topic, { qos: 0 }))
      if (username === 'admin' && password === 'openwb') {
        defaultCredentialsWarning.value = true
      }
    })
    client.on('close', () => {
      connected.value = false
    })
    client.on('offline', () => {
      connected.value = false
    })
    client.on('error', (error) => {
      console.error('MQTT error', error)
      // 135 not authorized, 137 bad credentials
      if (username !== undefined && error instanceof mqtt.ErrorWithReasonCode && [135, 137].includes(error.code)) {
        client?.end()
        removeCookie('mqtt')
        authFailureMessage.value = 'Die Anmeldeinformationen waren ungültig und wurden entfernt. Bitte die Seite neu laden.'
      }
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
      trackSocUpdate(topic)
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

  /** Resolves true once the broker has acknowledged the write; a refusal shows an error. */
  async function doPublish(topic: string, payload: unknown, retain = true, qos: QoS = 2): Promise<boolean> {
    if (!client) return false
    try {
      await client.publishAsync(topic, JSON.stringify(payload), { qos, retain })
      return true
    } catch (error) {
      console.error('MQTT publish failed', topic, error)
      showErrorToast('Die Änderung wurde nicht übernommen (fehlende Berechtigung oder Verbindungsfehler).')
      return false
    }
  }

  /** Patches a (nested) field of a received topic and republishes the whole value to its openWB/set/ counterpart (there are no per-field topics). A refused write restores the old value. */
  function updateTopic(topic: string, payload: unknown, objectPath?: string, publish = false): void {
    if (!(topic in topics.value)) {
      console.warn('updateTopic: topic not subscribed yet', topic)
      return
    }
    const original = JSON.parse(JSON.stringify(topics.value[topic])) as unknown
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
      void doPublish(topic.replace('openWB/', 'openWB/set/'), topics.value[topic]).then((ok) => {
        if (!ok) topics.value[topic] = original
      })
    }
  }

  /** Sends a backend command via command/<clientId>/todo/<command>. */
  function sendCommand(command: string, data: Record<string, unknown> = {}): void {
    void doPublish(`openWB/set/command/${clientId}/todo/${command}`, { command, data }, false)
  }

  // --- status strip --- (raw topics are in W and Wh, the getters return kW and kWh)

  const liveValues = computed(() => getValue.value<Partial<LiveValues>>('openWB/graph/lastlivevaluesJson', {}))
  /** False until the live feed has arrived (or if the role never gets it): the values below are 0 only for lack of data. */
  const liveValuesReceived = computed(() => 'openWB/graph/lastlivevaluesJson' in topics.value)
  // the live feed only has pv and battery fields when configured; roles without the configured flags rely on this
  const pvConfigured = computed(
    () => getValue.value<boolean>('openWB/pv/config/configured', false) || liveValues.value['pv-all'] !== undefined,
  )
  const batteryConfigured = computed(
    () =>
      getValue.value<boolean>('openWB/bat/config/configured', false) ||
      liveValues.value['bat-all-power'] !== undefined ||
      liveValues.value['bat-all-soc'] !== undefined,
  )
  const pvPower = computed(() => liveValues.value['pv-all'] ?? 0)
  const gridPower = computed(() => liveValues.value.grid ?? 0)
  const houseConsumption = computed(() => liveValues.value['house-power'] ?? 0)
  const houseDailyEnergy = computed(() => getValue.value<number>('openWB/counter/set/daily_yield_home_consumption', 0) / 1000)
  const houseTotalEnergy = computed(() => getValue.value<number>('openWB/counter/set/imported_home_consumption', 0) / 1000)
  const chargePointSumPower = computed(() => liveValues.value['charging-all'] ?? 0)
  const batteryPower = computed(() => liveValues.value['bat-all-power'] ?? 0)
  const batterySoc = computed(() => liveValues.value['bat-all-soc'] ?? 0)

  const electricityPriceConfigured = computed(() => getValue.value<boolean>('openWB/optional/ep/configured', false))
  const electricityPrices = computed(() => getValue.value<Record<string, number>>('openWB/optional/ep/get/prices', {}))
  // the backend prunes old prices only every few minutes, so the first entry can still be the slot that just ended
  const clock = ref(Date.now())
  setInterval(() => {
    clock.value = Date.now()
  }, 30_000)
  /** Price of the running slot: the latest entry that has started. */
  const currentElectricityPrice = computed<number | undefined>(() => {
    const entries = Object.entries(electricityPrices.value)
      .map(([timestamp, price]) => ({ start: Number(timestamp) * 1000, price }))
      .sort((a, b) => a.start - b.start)
    if (entries.length === 0) return undefined
    const running = [...entries].reverse().find((entry) => entry.start <= clock.value) ?? entries[0]
    return eurPerWhToCtPerKwh(running.price)
  })

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
  // not pruned server-side, so past slots are included
  const forecastSeries = computed(() =>
    Object.entries(forecastValues.value)
      .map(([timestamp, wh]) => ({ timestamp: Number(timestamp) * 1000, power: wh / 1000 }))
      .sort((a, b) => a.timestamp - b.timestamp),
  )
  const currentForecastPower = computed<number | undefined>(() => {
    const entries = forecastSeries.value
    if (entries.length === 0) return undefined
    return ([...entries].reverse().find((entry) => entry.timestamp <= clock.value) ?? entries[0]).power
  })
  /** Daily energy in kWh as the provider reports it. */
  function forecastDailyKwh(): Record<string, number> | undefined {
    return getValue.value<Record<string, number> | undefined>('openWB/optional/forecast/get/daily_kwh', undefined)
  }
  function forecastTodayKwh(): number | undefined {
    return getValue.value<number | undefined>('openWB/optional/forecast/get/today_kwh', undefined)
  }
  function forecastTomorrowKwh(): number | undefined {
    return getValue.value<number | undefined>('openWB/optional/forecast/get/tomorrow_kwh', undefined)
  }

  // --- access control (user management) ---

  /** Control rights come with a topic that only the roles allowed to write receive. A role that merely reads the configuration (installers, support) must not be offered the control. */
  function controlDataDelivered(topic: string): boolean {
    if (!userManagementKnown()) return false
    if (!userManagementActive()) return true
    return getValue.value<unknown>(topic, undefined) !== undefined
  }
  function vehicleSocEditable(vehicleId: number): boolean {
    return controlDataDelivered(`openWB/vehicle/${vehicleId}/soc_module/calculated_soc_state`)
  }
  // access flags: a user never receives 'true' for a section the role does not allow

  /** Readable for everyone; before it arrives nothing is known about the user's rights. */
  function userManagementKnown(): boolean {
    getValue.value('openWB/system/security/user_management_active', undefined)
    return 'openWB/system/security/user_management_active' in topics.value
  }
  function userManagementActive(): boolean {
    return getValue.value<boolean>('openWB/system/security/user_management_active', false)
  }
  function dataProtectionAcknowledged(): boolean {
    return getValue.value<boolean>('openWB/system/dataprotection_acknowledged', false)
  }
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
  /** The battery-control role is also the only one that may write the battery settings. */
  function accessBatteryControlAllowed(): boolean {
    return getValue.value<boolean>('openWB/system/security/access/ActiveBatControlConfiguration', false)
  }
  function accessChartAllowed(): boolean {
    return getValue.value<boolean>('openWB/system/security/access/Chart', false)
  }

  // --- login / user management ---

  // from the cookie, not reactive; login() and logout() reload the page right after changing it
  const loggedIn = computed(() => getCookie('mqtt') !== undefined)
  const username = computed(() => mqttCredentials().username ?? '')

  /** The backend answers the same way whether or not the user exists (anti-enumeration), so there is no completion signal to wait for. */
  function requestPasswordResetToken(resetUsername: string): void {
    sendCommand('createPasswordResetToken', { username: resetUsername })
  }
  function resetUserPassword(resetUsername: string, token: string, newPassword: string): void {
    sendCommand('resetUserPassword', { username: resetUsername, token, newPassword })
  }

  function login(loginUsername: string, loginPassword: string): void {
    setCookie('mqtt', `${loginUsername}:${loginPassword}`, 30)
    location.reload()
  }
  function logout(): void {
    removeCookie('mqtt')
    location.reload()
  }

  // --- live view (recent rolling window, finer-grained than the 5-min daily log) ---

  // alllivevaluesJson1-16 hold newline-separated JSON lines, so getValue leaves them as strings
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
            // partial line
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

  /** The grid counter is the root of the hierarchy (backend convention). */
  function gridCounterId(): number | undefined {
    const hierarchy = getValue.value<Hierarchy[]>('openWB/counter/get/hierarchy', [])
    return hierarchy[0]?.type === 'counter' ? hierarchy[0].id : undefined
  }

  function findHierarchyPath(nodes: Hierarchy[], targetId: number): Hierarchy[] | undefined {
    for (const node of nodes) {
      if (node.id === targetId) return [node]
      const childPath = findHierarchyPath(node.children, targetId)
      if (childPath) return [node, ...childPath]
    }
    return undefined
  }


  const chargePointIds = computed(() => getObjectIds('cp').filter(accessChargePointAllowed))
  const batteryIds = computed(() => getObjectIds('bat').filter(accessBatteryAllowed))
  const inverterIds = computed(() => getObjectIds('inverter').filter(accessComponentAllowed))
  const consumerIds = computed(() => getObjectIds('consumer').filter(accessConsumerAllowed))
  const counterIds = computed(() => getObjectIds('counter').filter(accessComponentAllowed))
  function gridCounterAccessible(): boolean {
    const id = gridCounterId()
    return id !== undefined && accessComponentAllowed(id)
  }

  /** The device id is unknown, hence a regex over the received topics (getWildcardValues only matches prefixes). */
  function getComponentConfiguration(id: number): ComponentConfiguration | undefined {
    const topic = `openWB/system/device/+/component/${id}/config`
    if (!(topic in subscriptions.value)) subscribe(topic)
    const pattern = new RegExp(`^${topic.replace(/\+/g, '[^/]+')}$`)
    for (const key in topics.value) {
      if (pattern.test(key)) return topics.value[key] as ComponentConfiguration
    }
    return undefined
  }

  function chargePointConfig(id: number): ChargePointConfig | undefined {
    return getValue.value<ChargePointConfig | undefined>(`openWB/chargepoint/${id}/config`, undefined)
  }
  function chargePointName(id: number): string {
    return chargePointConfig(id)?.name ?? `Ladepunkt ${id}`
  }
  /** A restricted role never receives this id's config, so "config received" doubles as the access check. */
  function accessChargePointAllowed(id: number): boolean {
    return chargePointConfig(id) !== undefined && controlDataDelivered(`openWB/chargepoint/${id}/set/manual_lock`)
  }

  function chargePointPlugState(id: number): boolean {
    return getValue.value<boolean>(`openWB/chargepoint/${id}/get/plug_state`, false)
  }
  function chargePointChargeState(id: number): boolean {
    return getValue.value<boolean>(`openWB/chargepoint/${id}/get/charge_state`, false)
  }
  function chargePointPower(id: number): number {
    return getValue.value<number>(`openWB/chargepoint/${id}/get/power`, 0) / 1000
  }
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
  /** The setpoint, not the phases currently in use. */
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
  function chargePointInstancePowers(id: number): number[] {
    return getValue.value<number[]>(`openWB/chargepoint/${id}/get/powers`, []).map((p) => p / 1000)
  }
  function chargePointInstancePowerFactors(id: number): number[] {
    return getValue.value<number[]>(`openWB/chargepoint/${id}/get/power_factors`, [])
  }
  function chargePointFrequency(id: number): number {
    return getValue.value<number>(`openWB/chargepoint/${id}/get/frequency`, 0)
  }
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
    // optimistic: the backend relay takes a moment
    const infoTopic = `openWB/chargepoint/${id}/get/connected_vehicle/info`
    const previous = topics.value[infoTopic]
    updateTopic(infoTopic, { id: vehicleId, name: vehicleName })
    void doPublish(`openWB/set/chargepoint/${id}/config/ev`, vehicleId).then((ok) => {
      if (!ok) topics.value[infoTopic] = previous
    })
  }
  /** SoC module type of the connected vehicle. A role that cannot read the vehicle configuration still gets the SoC the chargepoint reports ('reported'). */
  function chargePointConnectedVehicleSocType(id: number): string | undefined {
    const vehicleId = chargePointConnectedVehicleInfo(id)?.id
    if (vehicleId === undefined) return undefined
    return vehicleSocType(vehicleId) ?? (chargePointConnectedVehicleSoc(id)?.soc !== undefined ? 'reported' : undefined)
  }
  function chargePointConnectedVehicleSoc(id: number): ChargePointConnectedVehicleSoc | undefined {
    return getValue.value<ChargePointConnectedVehicleSoc | undefined>(
      `openWB/chargepoint/${id}/get/connected_vehicle/soc`,
      undefined,
    )
  }
  function chargePointConnectedVehicleEvTemplateId(id: number): number | undefined {
    return getValue.value<ChargePointConnectedVehicleConfig | undefined>(
      `openWB/chargepoint/${id}/get/connected_vehicle/config`,
      undefined,
    )?.ev_template
  }
  /** Whether the connected vehicle (not the hardware) can do bidi/V2H. */
  function chargePointConnectedVehicleBidiCapable(id: number): boolean {
    const templateId = chargePointConnectedVehicleEvTemplateId(id)
    if (templateId === undefined) return false
    return getValue.value<EvTemplate | undefined>(`openWB/vehicle/template/ev_template/${templateId}`, undefined)
      ?.bidi ?? false
  }

  function chargePointTemplate(id: number): ChargePointTemplate | undefined {
    const templateId = chargePointConfig(id)?.template
    if (templateId === undefined) return undefined
    return getValue.value<ChargePointTemplate | undefined>(`openWB/chargepoint/template/${templateId}`, undefined)
  }
  /** undefined while the config and template topics are loading. */
  function chargePointChargeType(id: number): 'AC' | 'DC' | undefined {
    return chargePointTemplate(id)?.charging_type
  }
  function chargePointDcMaxPower(id: number): number | undefined {
    const dcMaxCurrent = chargePointTemplate(id)?.dc_max_current
    return dcMaxCurrent === undefined ? undefined : convertDcCurrentToPower(dcMaxCurrent)
  }

  function chargePointChargeTemplate(id: number): ChargeTemplate | undefined {
    return getValue.value<ChargeTemplate | undefined>(`openWB/chargepoint/${id}/set/charge_template`, undefined)
  }
  function chargePointChargeMode(id: number): string | undefined {
    return chargePointChargeTemplate(id)?.chargemode.selected
  }
  function setChargePointChargeMode(id: number, mode: string): void {
    updateTopic(`openWB/chargepoint/${id}/set/charge_template`, mode, 'chargemode.selected', true)
  }
  /** path is dotted, e.g. 'chargemode.instant_charging.current' */
  function setChargePointChargeTemplateField(id: number, path: string, value: unknown): void {
    updateTopic(`openWB/chargepoint/${id}/set/charge_template`, value, path, true)
  }

  type PlanKind = 'scheduled' | 'time'
  const PLAN_ADD_COMMANDS: Record<PlanKind, string> = {
    scheduled: 'addChargeTemplateSchedulePlan',
    time: 'addChargeTemplateTimeChargingPlan',
  }
  /** The backend numbers plan ids across all templates, so a new plan is created by command, not by writing the array. */
  function addChargePlan(chargePointId: number, kind: PlanKind): void {
    const template = chargePointChargeTemplate(chargePointId)
    if (template === undefined) return
    sendCommand(PLAN_ADD_COMMANDS[kind], { template: template.id, chargepoint: chargePointId, changed_in_theme: true })
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

  function vehicleManualSoc(vehicleId: number): number {
    const state = getValue.value<Record<string, unknown>>(`openWB/vehicle/${vehicleId}/soc_module/calculated_soc_state`, {})
    return (state.manual_soc as number | undefined) ?? (state.soc_start as number | undefined) ?? 0
  }
  // chargePointId also updates that chargepoint's cached SoC display
  function setVehicleManualSoc(vehicleId: number, value: number, chargePointId?: number): void {
    void doPublish(`openWB/set/vehicle/${vehicleId}/soc_module/calculated_soc_state/manual_soc`, value).then((ok) => {
      if (!ok) return
      const vehicleSocTopic = `openWB/vehicle/${vehicleId}/get/soc`
      if (getValue.value<number | undefined>(vehicleSocTopic, undefined) !== undefined) {
        updateTopic(vehicleSocTopic, value)
      }
      if (chargePointId === undefined) return
      const cpTopic = `openWB/chargepoint/${chargePointId}/get/connected_vehicle/soc`
      if ((getValue.value<{ soc?: number }>(cpTopic, {})).soc !== undefined) {
        updateTopic(cpTopic, value, 'soc')
      }
    })
  }
  // force_soc_update is cleared when the fetch starts, so the spinner waits for the result
  const socUpdatePending = ref<Record<number, true>>({})
  const socUpdateTimers: Record<number, ReturnType<typeof setTimeout>> = {}
  const SOC_UPDATE_TIMEOUT_MS = 120_000
  const SOC_RESULT_TOPICS = ['soc', 'range', 'soc_timestamp', 'odometer', 'fault_state']

  function endSocUpdate(vehicleId: number): void {
    clearTimeout(socUpdateTimers[vehicleId])
    delete socUpdatePending.value[vehicleId]
  }
  function vehicleForceSocUpdate(vehicleId: number): void {
    clearTimeout(socUpdateTimers[vehicleId])
    socUpdatePending.value[vehicleId] = true
    socUpdateTimers[vehicleId] = setTimeout(() => endSocUpdate(vehicleId), SOC_UPDATE_TIMEOUT_MS)
    void doPublish(`openWB/set/vehicle/${vehicleId}/get/force_soc_update`, 1, false).then((ok) => {
      if (!ok) endSocUpdate(vehicleId)
    })
  }
  function trackSocUpdate(topic: string): void {
    if (!topic.startsWith('openWB/vehicle/')) return
    const match = /^openWB\/vehicle\/(\d+)\/get\/(\w+)$/.exec(topic)
    if (match && SOC_RESULT_TOPICS.includes(match[2])) endSocUpdate(Number(match[1]))
  }
  function vehicleSocUpdateInProgress(vehicleId: number): boolean {
    return socUpdatePending.value[vehicleId] !== undefined
  }

  function vehicleInfo(id: number): VehicleInfo | undefined {
    return getValue.value<VehicleInfo | undefined>(`openWB/vehicle/${id}/info`, undefined)
  }
  function vehicleSocType(id: number): string | undefined {
    return getValue.value<{ type?: string } | undefined>(`openWB/vehicle/${id}/soc_module/config`, undefined)?.type
  }
  function vehicleSocValue(id: number): number | undefined {
    return getValue.value<number | undefined>(`openWB/vehicle/${id}/get/soc`, undefined)
  }
  function vehicleRange(id: number): number | undefined {
    return getValue.value<number | undefined>(`openWB/vehicle/${id}/get/range`, undefined)
  }
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


  /** 1-based rank in the load-management order; a group's children share the group's rank. */
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

  /** At most 2 vehicles to chart: connected ones first, then others with an SoC. */
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
  /** Config never arrives for a restricted role, see accessChargePointAllowed. */
  function accessComponentAllowed(id: number): boolean {
    return getComponentConfiguration(id) !== undefined
  }
  function accessBatteryAllowed(id: number): boolean {
    return accessComponentAllowed(id)
  }
  function batteryInstanceSoc(id: number): number | undefined {
    return getValue.value<number | undefined>(`openWB/bat/${id}/get/soc`, undefined)
  }
  function batteryInstancePower(id: number): number {
    return getValue.value<number>(`openWB/bat/${id}/get/power`, 0) / 1000
  }
  function batteryInstanceDailyImported(id: number): number {
    return getValue.value<number>(`openWB/bat/${id}/get/daily_imported`, 0) / 1000
  }
  function batteryInstanceDailyExported(id: number): number {
    return getValue.value<number>(`openWB/bat/${id}/get/daily_exported`, 0) / 1000
  }
  function batteryInstanceImported(id: number): number {
    return getValue.value<number>(`openWB/bat/${id}/get/imported`, 0) / 1000
  }
  function batteryInstanceExported(id: number): number {
    return getValue.value<number>(`openWB/bat/${id}/get/exported`, 0) / 1000
  }
  function batteryInstanceCurrents(id: number): number[] {
    return getValue.value<number[]>(`openWB/bat/${id}/get/currents`, [])
  }
  /** Active battery control status (e.g. "Hält SoC bei X%"); empty when self-regulated. */
  function batteryInstanceStateMessage(id: number): string {
    return getValue.value<string>(`openWB/bat/${id}/get/state_str`, '')
  }
  function batteryInstanceFaultState(id: number): number {
    return getValue.value<number>(`openWB/bat/${id}/get/fault_state`, 0)
  }
  function batteryInstanceFaultMessage(id: number): string {
    return getValue.value<string>(`openWB/bat/${id}/get/fault_str`, '')
  }

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

  /** Global PV-surplus priority, not per battery. */
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

  function batteryPowerReserveActive(): boolean {
    return getValue.value<boolean>('openWB/general/chargemode_config/bat/power_reserve_active', false)
  }
  function setBatteryPowerReserveActive(active: boolean): void {
    updateTopic('openWB/general/chargemode_config/bat/power_reserve_active', active, undefined, true)
  }
  function batteryPowerReserve(): number {
    return getValue.value<number>('openWB/general/chargemode_config/bat/power_reserve', 2000) / 1000
  }
  function setBatteryPowerReserve(kw: number): void {
    updateTopic('openWB/general/chargemode_config/bat/power_reserve', Math.round(kw * 1000), undefined, true)
  }

  function batteryPowerDischargeActive(): boolean {
    return getValue.value<boolean>('openWB/general/chargemode_config/bat/power_discharge_active', false)
  }
  function setBatteryPowerDischargeActive(active: boolean): void {
    updateTopic('openWB/general/chargemode_config/bat/power_discharge_active', active, undefined, true)
  }
  function batteryPowerDischarge(): number {
    return getValue.value<number>('openWB/general/chargemode_config/bat/power_discharge', 1500) / 1000
  }
  function setBatteryPowerDischarge(kw: number): void {
    updateTopic('openWB/general/chargemode_config/bat/power_discharge', Math.round(kw * 1000), undefined, true)
  }

  // --- active battery control ---

  /** undefined while unknown, which differs from a confirmed false. */
  function batteryInstancePowerLimitControllable(id: number): boolean | undefined {
    return getValue.value<boolean | undefined>(`openWB/bat/${id}/get/power_limit_controllable`, undefined)
  }
  // activation is a liability-worded confirmation in the settings UI only, so there is no setter
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
  /** 'vehicle_charging' requires manual_mode 'manual_limit'. */
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
  function counterInstancePower(id: number): number {
    return getValue.value<number>(`openWB/counter/${id}/get/power`, 0) / 1000
  }
  function counterInstanceDailyImported(id: number): number {
    return getValue.value<number>(`openWB/counter/${id}/get/daily_imported`, 0) / 1000
  }
  function counterInstanceDailyExported(id: number): number {
    return getValue.value<number>(`openWB/counter/${id}/get/daily_exported`, 0) / 1000
  }
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
  function counterInstancePowers(id: number): number[] {
    return getValue.value<number[]>(`openWB/counter/${id}/get/powers`, []).map((p) => p / 1000)
  }
  function counterInstancePowerFactors(id: number): number[] {
    return getValue.value<number[]>(`openWB/counter/${id}/get/power_factors`, [])
  }
  function counterInstanceFaultState(id: number): number {
    return getValue.value<number>(`openWB/counter/${id}/get/fault_state`, 0)
  }
  /** 'auto_home_consumption' follows the nearest explicit counter ancestor (as in the backend). */
  function effectiveHomeConsumption(path: Hierarchy[], startIndex: number): boolean {
    for (let i = startIndex; i >= 0; i--) {
      const node = path[i]
      if (node.type !== 'counter') break
      const raw = getValue.value<string>(
        `openWB/counter/${node.id}/config/is_home_consumption_counter`,
        'auto_home_consumption',
      )
      if (raw !== 'auto_home_consumption') return raw === 'home_consumption'
    }
    return true
  }
  function counterInstanceIsHomeConsumption(id: number): boolean {
    const hierarchy = getValue.value<Hierarchy[]>('openWB/counter/get/hierarchy', [])
    const path = findHierarchyPath(hierarchy, id) ?? []
    return effectiveHomeConsumption(path, path.length - 1)
  }
  /** A counter with children is not split out of the house total (the backend adds only its local power). */
  function counterInstanceHasChildren(id: number): boolean {
    const hierarchy = getValue.value<Hierarchy[]>('openWB/counter/get/hierarchy', [])
    const path = findHierarchyPath(hierarchy, id)
    return (path?.[path.length - 1]?.children.length ?? 0) > 0
  }
  function counterInstanceIsHouseSplitPart(id: number): boolean {
    return counterInstanceIsHomeConsumption(id) && !counterInstanceHasChildren(id)
  }
  function counterInstanceFaultMessage(id: number): string {
    return getValue.value<string>(`openWB/counter/${id}/get/fault_str`, '')
  }

  /** Only a label; the general setting is readable for few roles, so a chargepoint's label is the fallback. */
  function rangeUnit(vehicleId?: number): string {
    const general = getValue.value<string | undefined>('openWB/general/range_unit', undefined)
    if (general) return general
    if (vehicleId !== undefined) {
      for (const connection of vehicleConnectionState(vehicleId)) {
        const unit = chargePointConnectedVehicleSoc(connection.id)?.range_unit
        if (unit) return unit
      }
    }
    return 'km'
  }

  // --- inverters (pv) ---

  function inverterName(id: number): string {
    return getComponentConfiguration(id)?.name ?? `Wechselrichter ${id}`
  }
  function inverterInstancePower(id: number): number {
    return getValue.value<number>(`openWB/pv/${id}/get/power`, 0) / 1000
  }
  function inverterInstanceDailyExported(id: number): number {
    return getValue.value<number>(`openWB/pv/${id}/get/daily_exported`, 0) / 1000
  }
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

  // --- consumers ---

  // consumers have their own config topic (no device/component entry)
  function consumerModuleConfig(id: number): ComponentConfiguration | undefined {
    return getValue.value<ComponentConfiguration | undefined>(`openWB/consumer/${id}/module`, undefined)
  }
  function consumerExtraMeterId(id: number): number | undefined {
    return getValue.value<number | null>(`openWB/consumer/${id}/extra_meter`, null) ?? undefined
  }
  function consumerInstanceIsHomeConsumption(id: number): boolean {
    // standalone consumers (not in the hierarchy) never count into the house
    const hierarchy = getValue.value<Hierarchy[]>('openWB/counter/get/hierarchy', [])
    const path = findHierarchyPath(hierarchy, id)
    if (path === undefined) return false
    const config = getValue.value<{ is_home_consumption_consumer?: string } | undefined>(
      `openWB/consumer/${id}/config`,
      undefined,
    )
    const raw = config?.is_home_consumption_consumer ?? 'auto_home_consumption'
    if (raw !== 'auto_home_consumption') return raw === 'home_consumption'
    return effectiveHomeConsumption(path, path.length - 2)
  }
  function consumerName(id: number): string {
    return consumerModuleConfig(id)?.name ?? `Verbraucher ${id}`
  }
  function accessConsumerAllowed(id: number): boolean {
    return consumerModuleConfig(id) !== undefined && controlDataDelivered(`openWB/consumer/${id}/usage`)
  }
  function consumerInstancePower(id: number): number {
    return getValue.value<number>(`openWB/consumer/${id}/get/power`, 0) / 1000
  }
  function consumerInstanceDailyImported(id: number): number {
    return getValue.value<number>(`openWB/consumer/${id}/get/daily_imported`, 0) / 1000
  }
  function consumerInstanceImported(id: number): number {
    return getValue.value<number>(`openWB/consumer/${id}/get/imported`, 0) / 1000
  }
  function consumerInstanceVoltages(id: number): number[] {
    return getValue.value<number[]>(`openWB/consumer/${id}/get/voltages`, [])
  }
  function consumerInstanceCurrents(id: number): number[] {
    return getValue.value<number[]>(`openWB/consumer/${id}/get/currents`, [])
  }
  function consumerInstancePowers(id: number): number[] {
    return getValue.value<number[]>(`openWB/consumer/${id}/get/powers`, []).map((p) => p / 1000)
  }
  function consumerInstanceFaultState(id: number): number {
    return getValue.value<number>(`openWB/consumer/${id}/get/fault_state`, 0)
  }
  function consumerInstanceFaultMessage(id: number): string {
    return getValue.value<string>(`openWB/consumer/${id}/get/fault_str`, '')
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
  // a set/ topic, read-only for the UI
  function consumerOnTime(id: number): number {
    return getValue.value<number>(`openWB/consumer/${id}/set/on_time`, 0)
  }
  function consumerTemperatures(id: number): { index: number; value: number }[] {
    // a sensor without a reading is null; it keeps its number but is not shown
    return getValue.value<(number | null)[]>(`openWB/consumer/${id}/get/temperatures`, [])
      .map((value, index) => ({ index, value }))
      .filter((sensor): sensor is { index: number; value: number } => typeof sensor.value === 'number')
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
  function setConsumerResetChargemodeField(id: number, path: string, value: unknown): void {
    updateTopic(`openWB/consumer/${id}/usage`, value, `reset_chargemode.${path}`, true)
  }

  // --- daily log (chart history) ---

  /** Only requests the payload; the caller subscribes the date-dependent topic (see useDailyLog). */
  function fetchDailyLog(date: Date = new Date()): void {
    const dateString =
      date.getFullYear().toString() +
      (date.getMonth() + 1).toString().padStart(2, '0') +
      date.getDate().toString().padStart(2, '0')
    sendCommand('getDailyLog', { date: dateString })
  }

  return {
    topics,
    connected,
    authFailureMessage,
    defaultCredentialsWarning,
    initialize,
    userManagementKnown,
    accessBatteryControlAllowed,
    gridCounterAccessible,
    accessChargePointAllowed,
    accessConsumerAllowed,
    vehicleSocEditable,
    rangeUnit,
    subscribe,
    unsubscribe,
    getValue,
    pvPower,
    gridPower,
    houseConsumption,
    chargePointSumPower,
    batteryPower,
    batterySoc,
    liveValuesReceived,
    batteryConfigured,
    pvConfigured,
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
    forecastDailyKwh,
    forecastTodayKwh,
    forecastTomorrowKwh,
    userManagementActive,
    dataProtectionAcknowledged,
    accessAllowed,
    accessSettingsAllowed,
    accessStatusAllowed,
    accessChargeLogAllowed,
    accessChartAllowed,
    loggedIn,
    username,
    requestPasswordResetToken,
    resetUserPassword,
    login,
    logout,
    fetchDailyLog,
    liveSeriesRaw,
    subscribeLiveSeries,
    unsubscribeLiveSeries,
    chargePointIds,
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
    chargePointManualLock,
    setChargePointManualLock,
    chargePointConnectedVehicleInfo,
    setChargePointConnectedVehicle,
    chargePointConnectedVehicleSoc,
    chargePointConnectedVehicleSocType,
    chargePointConnectedVehicleBidiCapable,
    chargePointChargeType,
    chargePointDcMaxPower,
    chargePointChargeTemplate,
    chargePointChargeMode,
    setChargePointChargeMode,
    setChargePointChargeTemplateField,
    addChargePlan,
    vehicleList,
    subscribeVehicleList,
    unsubscribeVehicleList,
    vehicleManualSoc,
    vehicleSocType,
    setVehicleManualSoc,
    vehicleForceSocUpdate,
    vehicleSocUpdateInProgress,
    vehicleInfo,
    vehicleSocValue,
    vehicleRange,
    vehicleSocTimestamp,
    vehicleOdometer,
    vehicleFaultState,
    vehicleFaultMessage,
    subscribeVehicleConnectionState,
    unsubscribeVehicleConnectionState,
    vehicleConnectionState,
    vehiclePriority,
    consumerPriority,
    topVehicleIds,
    batteryIds,
    inverterIds,
    consumerIds,
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
    counterInstanceIsHouseSplitPart,
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
    counterInstanceIsHomeConsumption,
    counterInstanceFaultMessage,
    inverterName,
    inverterInstancePower,
    inverterInstanceDailyExported,
    inverterInstanceExported,
    inverterInstanceCurrents,
    inverterInstanceFaultState,
    inverterInstanceFaultMessage,
    pvFaultStateTotal,
    consumerName,
    consumerInstancePower,
    consumerInstanceDailyImported,
    consumerInstanceImported,
    houseDailyEnergy,
    houseTotalEnergy,
    consumerInstanceVoltages,
    consumerInstanceCurrents,
    consumerInstancePowers,
    consumerInstanceFaultState,
    consumerInstanceFaultMessage,
    consumerInstanceStateMessage,
    consumerExtraMeterId,
    consumerInstanceIsHomeConsumption,
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
