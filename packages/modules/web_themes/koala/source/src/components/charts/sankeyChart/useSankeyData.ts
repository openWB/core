/**
 * Store adapter for the live Sankey diagram.
 */
import { computed } from 'vue';
import { useQuasar } from 'quasar';
import { useMqttStore } from 'src/stores/mqtt-store';
import {
  allocate,
  groupNodes,
  type AllocationResult,
  type DynamicNodeInput,
} from './energy-allocation';

// Aggregate chargepoints/consumers/counters into a single node once there are more than the threshold.
const GROUP_THRESHOLD = 3;
const CP_GROUP_ID = 'cp_group';
const CONSUMER_GROUP_ID = 'consumer_group';
const CONSUMER_HOUSE_GROUP_ID = 'consumer_house_group';
const CONSUMER_ID_PREFIX = 'consumer';
const COUNTER_GROUP_ID = 'counter_group';
const COUNTER_HOUSE_GROUP_ID = 'counter_house_group';
const COUNTER_ID_PREFIX = 'counter';

export function useSankeyData() {
  const mqttStore = useMqttStore();
  const $q = useQuasar();

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

  // Consumers and counters counted in the home consumption are drawn as parts
  // of the household node, the others as sinks of their own. Group each set on
  // its own so the two never collapse into one node.
  const groupInAndOut = (
    nodes: DynamicNodeInput[],
    label: string,
    houseGroupId: string,
    groupId: string,
  ) => {
    const group = (inHouse: boolean, id: string) =>
      groupNodes(
        nodes.filter((node) => (node.inHouse ?? false) === inHouse),
        { threshold: GROUP_THRESHOLD, id, label },
      ).map((node) => ({ ...node, inHouse }));
    return [...group(true, houseGroupId), ...group(false, groupId)];
  };

  const consumers = computed(() => {
    const inHouse = mqttStore.inHomeConsumption.consumerIds;
    const nodes = mqttStore.consumerIds.map((id) => ({
      id: `${CONSUMER_ID_PREFIX}${id}`,
      label: mqttStore.consumerName(id) || `Verbraucher ${id}`,
      power: num(mqttStore.consumerPower(id, 'value')),
      inHouse: inHouse.includes(id),
    }));
    return groupInAndOut(
      nodes,
      'Verbraucher',
      CONSUMER_HOUSE_GROUP_ID,
      CONSUMER_GROUP_ID,
    );
  });

  const counters = computed(() => {
    const { inHome, notInHome } = mqttStore.shownCounterIds;
    const node = (id: number, inHouse: boolean) => ({
      id: `${COUNTER_ID_PREFIX}${id}`,
      label: mqttStore.componentName(id) || `Zähler ${id}`,
      power: num(mqttStore.counterLocalPower('value', id)),
      inHouse,
    });
    return groupInAndOut(
      [
        ...inHome.map((id) => node(id, true)),
        ...notInHome.map((id) => node(id, false)),
      ],
      'Zähler',
      COUNTER_HOUSE_GROUP_ID,
      COUNTER_GROUP_ID,
    );
  });

  // Hybrid inverter/battery pairs: how much of each hybrid battery's charge is
  // covered by its own inverter's PV on the DC bus. pvPowerIndividual reports
  // production as negative; batteryPower reports charging as positive.
  const hybrid = computed(() =>
    mqttStore.hybridInverters.map(({ inverterId, batteryId }) => ({
      inverterPv: Math.max(
        0,
        -num(mqttStore.pvPowerIndividual(inverterId, 'value')),
      ),
      batteryCharge: Math.max(
        0,
        num(mqttStore.batteryPower(batteryId, 'value')),
      ),
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
      counters: counters.value,
      hybrid: hybrid.value,
    }),
  );

  // A small screen has no room for node names once the household splits into
  // a third column. The names are then hidden and listed in a legend instead.
  const compact = computed(() => {
    return $q.screen.lt.sm && allocation.value.houseParts.length > 0;
  });

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
      case 'house_rest':
        return cssVar('--q-home-stroke');
      case COUNTER_GROUP_ID:
      case COUNTER_HOUSE_GROUP_ID:
        return cssVar('--q-secondary-counter-stroke');
      case CP_GROUP_ID:
        return cssVar('--q-charge-point-stroke');
      case CONSUMER_GROUP_ID:
      case CONSUMER_HOUSE_GROUP_ID:
        return cssVar('--q-consumer');
    }
    if (id.startsWith('cp')) {
      const cpId = Number(id.slice(2));
      return (
        mqttStore.chargePointColor(cpId) || cssVar('--q-charge-point-stroke')
      );
    }
    if (id.startsWith(CONSUMER_ID_PREFIX)) {
      const consumerId = Number(id.slice(CONSUMER_ID_PREFIX.length));
      return mqttStore.consumerColor(consumerId) || cssVar('--q-consumer');
    }
    if (id.startsWith(COUNTER_ID_PREFIX)) {
      const counterId = Number(id.slice(COUNTER_ID_PREFIX.length));
      return (
        mqttStore.secondaryCounterColor(counterId) ||
        cssVar('--q-secondary-counter-stroke')
      );
    }
    return cssVar('--q-vehicle-stroke');
  };

  //Node-label color for dark mode / light mode.
  const labelColor = (): string => {
    if (typeof document === 'undefined') {
      return '#000000';
    }
    return getComputedStyle(document.body).color || '#000000';
  };

  return { allocation, compact, colorForNode, labelColor };
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
