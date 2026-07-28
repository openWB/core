/**
 * Store adapter for the live Sankey diagram.
 */
import { computed } from 'vue';
import { useMqttStore } from 'src/stores/mqtt-store';
import { allocate, type AllocationResult } from './energy-allocation';

export function useSankeyData() {
  const mqttStore = useMqttStore();

  const num = (value: unknown): number => Number(value) || 0;

  const chargePoints = computed(() =>
    mqttStore.chargePointIds.map((id) => ({
      id: `cp${id}`,
      label: mqttStore.chargePointName(id) || `Ladepunkt ${id}`,
      power: num(mqttStore.chargePointPower(id, 'value')),
    })),
  );

  // Consumers placeholder
  const consumers = computed(() => []);

  const allocation = computed<AllocationResult>(() =>
    allocate({
      grid: num(mqttStore.counterPower('value')),
      pv: mqttStore.pvConfigured ? num(mqttStore.pvPowerTotal('value')) : 0,
      battery: mqttStore.batteryConfigured
        ? num(mqttStore.batteryTotalPower('value'))
        : 0,
      chargePoints: chargePoints.value,
      consumers: consumers.value,
    }),
  );

  /**
   * Resolve the display color for a node id.
   */
  const colorForNode = (id: string): string => {
    switch (id) {
      case 'grid':
        return cssVar('--q-grid-stroke');
      case 'pv':
        return cssVar('--q-pv-stroke');
      case 'battery':
        return cssVar('--q-battery-stroke');
      case 'house':
        return cssVar('--q-home-stroke');
    }
    if (id.startsWith('cp')) {
      const cpId = Number(id.slice(2));
      return mqttStore.chargePointColor(cpId) || cssVar('--q-charge-point-stroke');
    }
    //placeholder
    return cssVar('--q-vehicle-stroke');
  };

  return { allocation, colorForNode };
}

/**
 * Read a CSS custom property as a concrete color string. Resolved against
 * document.body (not documentElement) so the `.body--dark` overrides apply.
 */
function cssVar(name: string): string {
  if (typeof document === 'undefined') {
    return '#888888';
  }
  const value = getComputedStyle(document.body).getPropertyValue(name).trim();
  return value || '#888888';
}
