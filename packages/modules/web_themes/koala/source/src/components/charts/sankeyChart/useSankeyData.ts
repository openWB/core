/**
 * Store adapter for the live Sankey diagram.
 */
import { computed } from 'vue';
import { useMqttStore } from 'src/stores/mqtt-store';
import {
  allocate,
  groupNodes,
  type AllocationResult,
  type DynamicNodeInput,
} from './energy-allocation';

// Aggregate chargepoints/consumers into a single node once there are more than the threshold.
const GROUP_THRESHOLD = 3;
const CP_GROUP_ID = 'cp_group';
const CONSUMER_GROUP_ID = 'consumer_group';

export function useSankeyData() {
  const mqttStore = useMqttStore();

  const num = (value: unknown): number => Number(value) || 0;

  const chargePoints = computed(() =>
    groupNodes(
      mqttStore.chargePointIds.map((id) => ({
        id: `cp${id}`,
        label: mqttStore.chargePointName(id) || `Ladepunkt ${id}`,
        power: num(mqttStore.chargePointPower(id, 'value')),
      })),
      { threshold: GROUP_THRESHOLD, id: CP_GROUP_ID, label: 'Ladepunkte' },
    ),
  );

  // Consumer placeholder
  const consumers = computed(() =>
    groupNodes([] as DynamicNodeInput[], {
      threshold: GROUP_THRESHOLD,
      id: CONSUMER_GROUP_ID,
      label: 'Verbraucher',
    }),
  );

  // Hybrid inverter/battery pairs: how much of each hybrid battery's charge is
  // covered by its own inverter's PV on the DC bus. pvPowerIndividual reports
  // production as negative; batteryPower reports charging as positive.
  const hybrid = computed(() =>
    mqttStore.hybridInverters.map(({ inverterId, batteryId }) => ({
      inverterPv: Math.max(0, -num(mqttStore.pvPowerIndividual(inverterId, 'value'))),
      batteryCharge: Math.max(0, num(mqttStore.batteryPower(batteryId, 'value'))),
    })),
  );

  const allocation = computed<AllocationResult>(() =>
    allocate({
      grid: num(mqttStore.counterPower('value')),
      pv: mqttStore.pvConfigured ? num(mqttStore.pvPowerTotal('value')) : 0,
      battery: mqttStore.batteryConfigured
        ? num(mqttStore.batteryTotalPower('value'))
        : 0,
      chargePoints: chargePoints.value,
      consumers: consumers.value,
      hybrid: hybrid.value,
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
      case CP_GROUP_ID:
        return cssVar('--q-charge-point-stroke');
      case CONSUMER_GROUP_ID:
        return cssVar('--q-vehicle-stroke');
    }
    if (id.startsWith('cp')) {
      const cpId = Number(id.slice(2));
      return mqttStore.chargePointColor(cpId) || cssVar('--q-charge-point-stroke');
    }
    // Placeholder
    return cssVar('--q-vehicle-stroke');
  };


  //Node-label color for dark mode / light mode.
  const labelColor = (): string => {
    if (typeof document === 'undefined') {
      return '#000000';
    }
    return getComputedStyle(document.body).color || '#000000';
  };

  return { allocation, colorForNode, labelColor };
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
