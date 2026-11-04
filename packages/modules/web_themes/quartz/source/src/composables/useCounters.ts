import { computed, onMounted, onUnmounted } from 'vue'
import { useMqttStore } from '@/stores/mqtt-store'

/** Subscribes the component hierarchy for as long as the caller is mounted (same topic chargepoints already use). */
export function useCounters() {
  const mqttStore = useMqttStore()

  onMounted(() => mqttStore.subscribeComponentHierarchy())
  onUnmounted(() => mqttStore.unsubscribeComponentHierarchy())

  // non-grid sub-meters only - the grid/EVU connection itself is already shown as "Netz",
  // matching both koala's own precedent and the existing Zähler chart category
  const counterIds = computed(() => mqttStore.counterIds.filter((id) => id !== mqttStore.gridCounterId()))

  return { counterIds }
}
