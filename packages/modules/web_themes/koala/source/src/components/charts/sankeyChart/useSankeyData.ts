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
} from './energy-allocation';

// Aggregate chargepoints/consumers into a single node once there are more than the threshold.
const GROUP_THRESHOLD = 3;
const CP_GROUP_ID = 'cp_group';
const CONSUMER_GROUP_ID = 'consumer_group';
const CONSUMER_HOUSE_GROUP_ID = 'consumer_house_group';
const CONSUMER_ID_PREFIX = 'consumer';

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

  // Consumers counted in the home consumption are drawn as parts of the
  // household node, the others as sinks of their own. Group each set on its
  // own so the two never collapse into one node.
  const consumers = computed(() => {
    const inHouse = mqttStore.inHomeConsumption.consumerIds;
    const nodes = mqttStore.consumerIds.map((id) => ({
      id: `${CONSUMER_ID_PREFIX}${id}`,
      label: mqttStore.consumerName(id) || `Verbraucher ${id}`,
      power: num(mqttStore.consumerPower(id, 'value')),
      inHouse: inHouse.includes(id),
    }));
    const group = (inHouseSet: boolean, id: string) =>
      groupNodes(
        nodes.filter((node) => node.inHouse === inHouseSet),
        { threshold: GROUP_THRESHOLD, id, label: 'Verbraucher' },
      ).map((node) => ({ ...node, inHouse: inHouseSet }));
    return [
      ...group(true, CONSUMER_HOUSE_GROUP_ID),
      ...group(false, CONSUMER_GROUP_ID),
    ];
  });

  // Hybrid inverter/battery pairs: how much of each hybrid battery's charge is
  // covered by its own inverter's PV on the DC bus. pvPowerIndividual reports
  // production as negative; batteryPower reports charging as positive.
  const hybrid = computed(() =>
    mqttStore.hybridInverters.map(({ inverterId, batteryId }) => ({
      inverterPv: Math.max(0, -num(mqttStore.pvPowerIndividual(inverterId, 'value'))),
      batteryCharge: Math.max(0, num(mqttStore.batteryPower(batteryId, 'value'))),
    })),
  );

  // What is not counted in the home consumption and is no consumer: the
  // sub-counters set to "Nein". The backend publishes only the sum, so the
  // consumers, which are sinks of their own, are taken out of it.
  const notInHomeOther = computed(() => {
    const { consumerIds, counterIds } = mqttStore.notInHomeConsumption;
    if (counterIds.length === 0) {
      return 0;
    }
    const consumerPower = consumerIds.reduce(
      (total, id) => total + num(mqttStore.consumerPower(id, 'value')),
      0,
    );
    return num(mqttStore.notInHomeConsumptionPower('value')) - consumerPower;
  });

  const allocation = computed<AllocationResult>(() =>
    allocate({
      grid: num(mqttStore.counterPower('value')),
      pv: mqttStore.pvConfigured ? num(mqttStore.pvPowerTotal('value')) : 0,
      battery: mqttStore.batteryConfigured
        ? num(mqttStore.batteryTotalPower('value'))
        : 0,
      chargePoints: chargePoints.value,
      consumers: consumers.value,
      notInHomeOther: notInHomeOther.value,
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
      case 'not_in_home':
        return cssVar('--q-secondary-counter-stroke');
      case CP_GROUP_ID:
        return cssVar('--q-charge-point-stroke');
      case CONSUMER_GROUP_ID:
      case CONSUMER_HOUSE_GROUP_ID:
        return cssVar('--q-consumer');
    }
    if (id.startsWith('cp')) {
      const cpId = Number(id.slice(2));
      return mqttStore.chargePointColor(cpId) || cssVar('--q-charge-point-stroke');
    }
    if (id.startsWith(CONSUMER_ID_PREFIX)) {
      const consumerId = Number(id.slice(CONSUMER_ID_PREFIX.length));
      return mqttStore.consumerColor(consumerId) || cssVar('--q-consumer');
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
