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

  const consumerIds = computed(() => mqttStore.consumerIds)
  // consumers inside the house consumption stay out of chip, flow and chart, but keep their card
  const visibleConsumerIds = computed(() => consumerIds.value.filter((id) => !mqttStore.consumerInstanceIsHomeConsumption(id)))
  const homeConsumptionConsumerIds = computed(() => consumerIds.value.filter((id) => mqttStore.consumerInstanceIsHomeConsumption(id)))
  const visibleConsumerPower = computed(() =>
    visibleConsumerIds.value.reduce((sum, id) => sum + mqttStore.consumerInstancePower(id), 0),
  )

  return { consumerIds, visibleConsumerIds, homeConsumptionConsumerIds, visibleConsumerPower }
}
