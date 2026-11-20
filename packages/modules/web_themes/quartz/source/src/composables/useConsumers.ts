import { computed, onMounted, onUnmounted } from 'vue'
import { useMqttStore } from '@/stores/mqtt-store'

/** Subscribes the component hierarchy and priority list for as long as the caller is mounted. */
export function useConsumers() {
  const mqttStore = useMqttStore()

  onMounted(() => {
    mqttStore.subscribeComponentHierarchy()
    mqttStore.subscribeLoadmanagementPrios()
  })
  onUnmounted(() => {
    mqttStore.unsubscribeComponentHierarchy()
    mqttStore.unsubscribeLoadmanagementPrios()
  })

  return { consumerIds: computed(() => mqttStore.consumerIds) }
}
