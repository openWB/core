import { computed, type Ref } from 'vue'
import { useMqttStore, type RawLivePoint } from '@/stores/mqtt-store'
import type { CategoryData, CategoryKey, InstancePoint, InstanceSeries } from '@/types/chart'

const INSTANCE_KEY = /^(cp|consumer|counter)(\d+)-power$/

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

  const categories = computed<Record<CategoryKey, CategoryData>>(() => {
    const cutoff = Date.now() - rangeMinutes.value * 60 * 1000
    const points = mqttStore.liveSeriesRaw.filter((entry) => entry.timestamp * 1000 >= cutoff)

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

    points.forEach((entry: RawLivePoint) => {
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

    const toSeries = (map: Map<string, InstancePoint[]>, labelPrefix: string): InstanceSeries[] =>
      Array.from(map.entries()).map(([id, pts]) => ({ id, label: `${labelPrefix} ${id.replace(/\D/g, '')}`, points: pts }))

    return {
      pv: { all: pv, individual: [] },
      grid: { all: grid, individual: [] },
      house: { all: house, individual: [] },
      battery: { all: battery, individual: [] },
      consumer: { all: consumerAll, individual: toSeries(consumerInstances, 'Verbraucher') },
      chargepoint: { all: chargepointAll, individual: toSeries(cpInstances, 'Ladepunkt') },
      counter: { all: counterAll, individual: toSeries(counterInstances, 'Zähler') },
    }
  })

  return { categories }
}
