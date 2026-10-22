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

  function doPublish(topic: string, payload: unknown, retain = true, qos: QoS = 0): void {
    client?.publish(topic, JSON.stringify(payload), { qos, retain })
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
  const chargePointPower = computed(() => liveValues.value['charging-all'] ?? 0)
  const batteryPower = computed(() => liveValues.value['bat-all-power'] ?? 0)
  const batterySoc = computed(() => liveValues.value['bat-all-soc'] ?? 0)

  const electricityPriceConfigured = computed(() => getValue.value<boolean>('openWB/optional/ep/configured', false))
  const electricityPrices = computed(() => getValue.value<Record<string, number>>('openWB/optional/ep/get/prices', {}))
  // prices are pruned server-side to "now or later" (see ElectricityPricingCard.vue), so the first entry is current
  const currentElectricityPrice = computed<number | undefined>(() => {
    const entries = Object.values(electricityPrices.value)
    return entries.length > 0 ? entries[0] * 100000 : undefined
  })

  const forecastConfigured = computed(() => getValue.value<boolean>('openWB/optional/forecast/configured', false))
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
    chargePointPower,
    batteryPower,
    batterySoc,
    electricityPriceConfigured,
    currentElectricityPrice,
    forecastConfigured,
    forecastSeries,
    currentForecastPower,
    fetchDailyLog,
  }
})
