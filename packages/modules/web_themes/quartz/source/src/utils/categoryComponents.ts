import type { useMqttStore } from '@/stores/mqtt-store'
import type { CategoryKey } from '@/types/chart'

/** Whether a chart category has a component behind it. 'counter' has no static signal (grid vs. other is a runtime flag), so the number of its lines in the loaded data is passed in. Shared by the legend and the theme settings. */
export function categoryHasComponent(
  key: CategoryKey,
  mqttStore: ReturnType<typeof useMqttStore>,
  counterLineCount: number,
): boolean {
  switch (key) {
    case 'grid':
    case 'house':
      return true
    // the live feed carries these lines even for a user who may not see the components
    case 'pv':
      return mqttStore.pvConfigured || mqttStore.inverterIds.length > 0
    case 'battery':
      return mqttStore.batteryConfigured || mqttStore.batteryIds.length > 0
    case 'chargepoint':
      return mqttStore.chargePointIds.length > 0
    case 'consumer':
      // consumers counted into the house consumption belong to the house line
      return mqttStore.consumerIds.some((id) => !mqttStore.consumerInstanceIsHomeConsumption(id))
    case 'counter':
      return counterLineCount > 0
  }
}
