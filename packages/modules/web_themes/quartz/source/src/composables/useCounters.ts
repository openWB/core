import { computed } from 'vue'
import { useMqttStore } from '@/stores/mqtt-store'

export function useCounters() {
  const mqttStore = useMqttStore()

  // the grid counter is shown as "Netz"
  const subMeterIds = computed(() => mqttStore.counterIds.filter((id) => id !== mqttStore.gridCounterId()))
  // counters inside the house consumption are part of "Haus"
  const counterIds = computed(() => subMeterIds.value.filter((id) => !mqttStore.counterInstanceIsHomeConsumption(id)))
  const homeConsumptionCounterIds = computed(() => subMeterIds.value.filter((id) => mqttStore.counterInstanceIsHomeConsumption(id)))

  const houseSplitCounterIds = computed(() => subMeterIds.value.filter((id) => mqttStore.counterInstanceIsHouseSplitPart(id)))
  const counterPower = computed(() => counterIds.value.reduce((sum, id) => sum + mqttStore.counterInstancePower(id), 0))

  return { counterIds, homeConsumptionCounterIds, houseSplitCounterIds, counterPower }
}
