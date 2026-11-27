import { computed, onMounted, onUnmounted } from 'vue'
import { useMqttStore } from '@/stores/mqtt-store'

/** The vehicle list feeds the vehicle selector of the chargepoint cards. */
export function useChargePoints() {
  const mqttStore = useMqttStore()

  onMounted(() => mqttStore.subscribeVehicleList())
  onUnmounted(() => mqttStore.unsubscribeVehicleList())

  return { chargePointIds: computed(() => mqttStore.chargePointIds) }
}
