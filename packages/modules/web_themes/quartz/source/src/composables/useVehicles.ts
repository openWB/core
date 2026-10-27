import { computed, onMounted, onUnmounted } from 'vue'
import { useMqttStore } from '@/stores/mqtt-store'

/** Subscribes the vehicle-list and cross-chargepoint connection-state feeds for as long as the caller is mounted. */
export function useVehicles() {
  const mqttStore = useMqttStore()

  onMounted(() => {
    mqttStore.subscribeVehicleList()
    mqttStore.subscribeVehicleConnectionState()
    mqttStore.subscribeLoadmanagementPrios()
  })
  onUnmounted(() => {
    mqttStore.unsubscribeVehicleList()
    mqttStore.unsubscribeVehicleConnectionState()
    mqttStore.unsubscribeLoadmanagementPrios()
  })

  // only vehicles whose /info has actually arrived - matches koala's own vehicle-list filter,
  // excludes ids that exist in /name but never finished publishing (transitional/broken state)
  const vehicleIds = computed(() =>
    mqttStore.vehicleList.filter((v) => mqttStore.vehicleInfo(v.id) !== undefined).map((v) => v.id),
  )

  return { vehicleIds }
}
