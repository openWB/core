import { computed } from 'vue'
import { useMqttStore } from '@/stores/mqtt-store'

export function useBatteries() {
  const mqttStore = useMqttStore()

  // with more than one battery, -1 stands for the overview card
  const batteryIds = computed(() => {
    const ids = mqttStore.batteryIds
    return ids.length > 1 ? [-1, ...ids] : ids
  })

  return { batteryIds }
}
