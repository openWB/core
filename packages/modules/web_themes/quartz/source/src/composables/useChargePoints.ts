import { computed, onMounted, onUnmounted } from 'vue'
import { useMqttStore } from '@/stores/mqtt-store'

/** Subscribes the chargepoint-list and vehicle-list feeds for as long as the caller is mounted. */
export function useChargePoints() {
  const mqttStore = useMqttStore()

  onMounted(() => {
    mqttStore.subscribeChargePointList()
    mqttStore.subscribeVehicleList()
  })
  onUnmounted(() => {
    mqttStore.unsubscribeChargePointList()
    mqttStore.unsubscribeVehicleList()
  })

  // wrapped in its own computed, not returned as a bare store property - a bare read would
  // snapshot the value once (often before the hierarchy topic has even arrived) and never update
  return { chargePointIds: computed(() => mqttStore.chargePointIds) }
}
