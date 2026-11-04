import { computed, type Ref } from 'vue'
import { useMqttStore, type RawLivePoint } from '@/stores/mqtt-store'
import type {
  CategoryData,
  CategoryKey,
  InstancePoint,
  InstanceSeries,
  SocCategoryData,
  SocPoint,
  SocSeries,
} from '@/types/chart'

const INSTANCE_KEY = /^(cp|consumer|counter)(\d+)-power$/
const EV_SOC_KEY = /^ev(\d+)-soc$/

/**
 * Finer-grained recent-window series than the daily log - see koala's alllivevaluesJson*
 * chunks (runs/graphing.sh). Unlike the daily log, this feed only carries per-instance
 * breakdown for chargepoints, consumers and (non-grid) counters - pv/battery are only ever
 * published as totals, so their 'individual' arrays are always empty here. The backend never
 * publishes a 'counterN-power' for the grid counter itself (see graph.py::pub_graph_data), so
 * unlike the daily log's buildCounterCategory, no grid-flag filtering is needed here. There's
 * also no combined 'counter-all' key, so the total is summed client-side from the per-instance
 * fields. Subscription lifecycle is the caller's responsibility
 * (mqttStore.subscribeLiveSeries/unsubscribeLiveSeries), since it's only needed while live view
 * is actually selected.
 */
export function useLiveView(rangeMinutes: Ref<number>) {
  const mqttStore = useMqttStore()

  const points = computed(() => {
    const cutoff = Date.now() - rangeMinutes.value * 60 * 1000
    return mqttStore.liveSeriesRaw.filter((entry) => entry.timestamp * 1000 >= cutoff)
  })

  const categories = computed<Record<CategoryKey, CategoryData>>(() => {
    const pv: InstancePoint[] = []
    const grid: InstancePoint[] = []
    const house: InstancePoint[] = []
    const battery: InstancePoint[] = []
    const consumerAll: InstancePoint[] = []
    const chargepointAll: InstancePoint[] = []
    const counterAll: InstancePoint[] = []
    const cpInstances = new Map<string, InstancePoint[]>()
    const consumerInstances = new Map<string, InstancePoint[]>()
    const counterInstances = new Map<string, InstancePoint[]>()

    points.value.forEach((entry: RawLivePoint) => {
      const timestamp = entry.timestamp * 1000
      pv.push({ timestamp, power: entry['pv-all'] ?? 0 })
      grid.push({ timestamp, power: entry.grid ?? 0 })
      house.push({ timestamp, power: entry['house-power'] ?? 0 })
      battery.push({ timestamp, power: entry['bat-all-power'] ?? 0 })
      consumerAll.push({ timestamp, power: entry['consumer-all'] ?? 0 })
      chargepointAll.push({ timestamp, power: entry['charging-all'] ?? 0 })

      let counterSum = 0
      Object.keys(entry).forEach((key) => {
        const match = key.match(INSTANCE_KEY)
        if (!match) return
        const [, group, num] = match
        const value = entry[key] ?? 0
        const id = `${group}${num}`
        if (group === 'counter') {
          counterSum += value
          if (!counterInstances.has(id)) counterInstances.set(id, [])
          counterInstances.get(id)?.push({ timestamp, power: value })
          return
        }
        const map = group === 'cp' ? cpInstances : consumerInstances
        if (!map.has(id)) map.set(id, [])
        map.get(id)?.push({ timestamp, power: value })
      })
      counterAll.push({ timestamp, power: counterSum })
    })

    // real names (not a generic "Zähler <id>"-style fallback) - the live feed itself carries no
    // name data, but the real component config is already available via the store's own
    // getComponentConfiguration-backed getters, same ones the cards/popups already use
    const toSeries = (map: Map<string, InstancePoint[]>, resolveName: (id: number) => string): InstanceSeries[] =>
      Array.from(map.entries()).map(([id, pts]) => ({
        id,
        label: resolveName(Number(id.replace(/\D/g, ''))),
        points: pts,
      }))

    return {
      pv: { all: pv, individual: [] },
      grid: { all: grid, individual: [] },
      house: { all: house, individual: [] },
      battery: { all: battery, individual: [] },
      consumer: { all: consumerAll, individual: toSeries(consumerInstances, mqttStore.consumerName) },
      chargepoint: { all: chargepointAll, individual: toSeries(cpInstances, mqttStore.chargePointName) },
      counter: { all: counterAll, individual: toSeries(counterInstances, mqttStore.counterName) },
    }
  })

  // only the aggregate 'bat-all-soc' is published to the live feed (graph.py) - no per-battery
  // breakdown there, unlike the daily log, so individual stays empty (same asymmetry the
  // 'battery' power category above already has between day and live mode)
  const batterySoc = computed<SocCategoryData>(() => ({
    all: points.value
      .filter((entry) => entry['bat-all-soc'] !== undefined)
      .map((entry) => ({ timestamp: entry.timestamp * 1000, soc: entry['bat-all-soc'] as number })),
    individual: [],
  }))

  const vehicleSocAll = computed<SocSeries[]>(() => {
    const instancePoints = new Map<string, SocPoint[]>()
    points.value.forEach((entry: RawLivePoint) => {
      const timestamp = entry.timestamp * 1000
      Object.keys(entry).forEach((key) => {
        const match = key.match(EV_SOC_KEY)
        if (!match) return
        const [, num] = match
        const value = entry[key]
        if (value === undefined) return
        if (!instancePoints.has(num)) instancePoints.set(num, [])
        instancePoints.get(num)?.push({ timestamp, soc: value })
      })
    })
    return Array.from(instancePoints.entries()).map(([id, pts]) => ({
      id,
      label: `Fahrzeug ${id}`,
      points: pts,
    }))
  })

  return { categories, batterySoc, vehicleSocAll }
}
