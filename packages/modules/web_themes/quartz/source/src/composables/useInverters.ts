import { computed, onMounted, onUnmounted } from 'vue'
import { useMqttStore } from '@/stores/mqtt-store'

/** Subscribes the component hierarchy for as long as the caller is mounted (same topic chargepoints already use). */
export function useInverters() {
  const mqttStore = useMqttStore()

  onMounted(() => mqttStore.subscribeComponentHierarchy())
  onUnmounted(() => mqttStore.unsubscribeComponentHierarchy())

  return { inverterIds: computed(() => mqttStore.inverterIds) }
}
