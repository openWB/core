import { computed, onMounted, onUnmounted } from 'vue'
import { useMqttStore } from '@/stores/mqtt-store'

/** Subscribes the component hierarchy for as long as the caller is mounted (same topic chargepoints already use). */
export function useBatteries() {
  const mqttStore = useMqttStore()

  onMounted(() => mqttStore.subscribeChargePointList())
  onUnmounted(() => mqttStore.unsubscribeChargePointList())

  // prepend the overview pseudo-id (-1) once there's more than one battery - matches koala's own BatteryInformation.vue
  const batteryIds = computed(() => {
    const ids = mqttStore.batteryIds
    return ids.length > 1 ? [-1, ...ids] : ids
  })

  return { batteryIds }
}
