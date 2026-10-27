import { computed, onMounted, onUnmounted } from 'vue'
import { useMqttStore } from '@/stores/mqtt-store'

/** Subscribes the component hierarchy and priority list for as long as the caller is mounted. */
export function useConsumers() {
  const mqttStore = useMqttStore()

  onMounted(() => {
    mqttStore.subscribeChargePointList()
    mqttStore.subscribeLoadmanagementPrios()
  })
  onUnmounted(() => {
    mqttStore.unsubscribeChargePointList()
    mqttStore.unsubscribeLoadmanagementPrios()
  })

  return { consumerIds: computed(() => mqttStore.consumerIds) }
}
