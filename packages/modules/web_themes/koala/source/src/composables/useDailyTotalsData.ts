import { computed } from 'vue';
import { useMqttStore } from 'src/stores/mqtt-store';
import type { DailyTotalsItem } from 'src/components/models/daily-totals-model';

/**
 * Direction of the power arrow for one daily totals entry. Counters point
 * the other way round: negative power means feed-in.
 */
export const powerArrow = (item: DailyTotalsItem) => {
  const value = item.powerValue ?? 0;
  const noCurrent = !Number.isFinite(value) || value === 0;
  const isCounter = item.id === 'grid' || item.id.startsWith('counter-');
  return {
    noCurrent,
    rotate180: !noCurrent && (isCounter ? value < 0 : value > 0),
  };
};

/**
 * Current power and daily totals per component type, shared by the
 * "Tageswerte" carousel slide and the desktop daily totals strip.
 */
export const useDailyTotalsData = () => {
  const mqttStore = useMqttStore();
  const gridPower = computed(() => mqttStore.counterPower('value'));
  const showGrid = computed(
    () =>
      gridPower.value !== undefined ||
      secondaryComponentsConfigured.value('counter'),
  );

  const showHomePower = computed(() => {
    return mqttStore.homePower('value') !== undefined;
  });
  const batteryConfigured = computed(() => mqttStore.batteryConfigured);
  const pvConfigured = computed(() => mqttStore.pvConfigured);
  const consumerConfigured = computed(() => mqttStore.consumerIds.length > 0);
  const chargePointSumPowerAvailable = computed(
    () => mqttStore.chargePointSumPower('value') !== undefined,
  );
  const chargePointConfigured = computed(
    () => mqttStore.chargePointIds.length > 0,
  );
  const secondaryComponentsConfigured = computed(() => {
    return (componentType: string): boolean => {
      switch (componentType) {
        case 'counter':
          return secondaryCounterData.value.length > 0;
        case 'chargepoint':
          return individualChargePointData.value.length > 1;
        case 'battery':
          return individualBatteryData.value.length > 1;
        case 'pv':
          return individualPvData.value.length > 1;
        case 'consumer':
          return individualConsumerData.value.length > 1;
        default:
          return false;
      }
    };
  });

  const gridData = computed((): DailyTotalsItem => {
    let data: DailyTotalsItem = {
      id: 'grid',
      title: 'Zähler',
      level: 'primary',
      icon: 'grid',
    };
    if (gridPower.value !== undefined) {
      data = {
        ...data,
        title: 'Netz',
        icon: 'grid',
        power: mqttStore.counterPower('textValue') as string,
        powerValue: mqttStore.counterPower('value') as number,
        today: {
          imported: mqttStore.counterDailyImported('textValue') as string,
          exported: mqttStore.counterDailyExported('textValue') as string,
        },
        color: 'var(--q-grid-stroke)',
      };
    }
    return data;
  });

  const secondaryCounterData = computed((): DailyTotalsItem[] => {
    const counters: DailyTotalsItem[] = [];
    mqttStore.secondaryCounterIds.forEach((id) => {
      const name = mqttStore.componentName(id);
      if (name !== undefined) {
        counters.push({
          id: `counter-${id}`,
          title: name,
          level: 'secondary',
          icon: 'counter',
          power: mqttStore.counterPower('textValue', id) as string,
          powerValue: mqttStore.counterPower('value', id) as number,
          today: {
            imported: mqttStore.counterDailyImported('textValue', id) as string,
            exported: mqttStore.counterDailyExported('textValue', id) as string,
          },
          color:
            mqttStore.gridComponentColor(id) ||
            'var(--q-secondary-counter-stroke)',
        });
      }
    });
    return counters;
  });

  const individualChargePointData = computed((): DailyTotalsItem[] => {
    const chargePoints: DailyTotalsItem[] = [];
    mqttStore.chargePointIds.forEach((id) => {
      const name = mqttStore.chargePointName(id);
      if (name !== undefined) {
        chargePoints.push({
          id: `chargepoint-${id}`,
          title: name,
          level: 'secondary',
          icon: 'chargepoint',
          power: mqttStore.chargePointPower(id, 'textValue') as string,
          powerValue: mqttStore.chargePointPower(id, 'value') as number,
          today: {
            imported: mqttStore.chargePointDailyImported(
              'textValue',
              id,
            ) as string,
            exported: mqttStore.chargePointDailyExported(
              'textValue',
              id,
            ) as string,
          },
          color:
            mqttStore.chargePointColor(id) || 'var(--q-charge-point-stroke)',
        });
      }
    });
    return chargePoints;
  });

  const individualBatteryData = computed((): DailyTotalsItem[] => {
    const batteries: DailyTotalsItem[] = [];

    mqttStore.batteryIds.forEach((id) => {
      const name = mqttStore.batteryName(id);
      if (name !== undefined) {
        batteries.push({
          id: `battery-${id}`,
          title: name,
          level: 'secondary',
          icon: 'battery',
          soc: mqttStore.batterySoc(id),
          power: mqttStore.batteryPower(id, 'textValue') as string,
          powerValue: mqttStore.batteryPower(id, 'value') as number,
          today: {
            imported: mqttStore.batteryDailyImported(id, 'textValue') as string,
            exported: mqttStore.batteryDailyExported(id, 'textValue') as string,
          },
          color: mqttStore.batteryColor(id) || 'var(--q-battery-stroke)',
        });
      }
    });
    return batteries;
  });

  const individualPvData = computed((): DailyTotalsItem[] => {
    const pvSystems: DailyTotalsItem[] = [];

    mqttStore.pvIds.forEach((id) => {
      const name = mqttStore.componentName(id);
      if (name !== undefined) {
        pvSystems.push({
          id: `pv-${id}`,
          title: name,
          level: 'secondary',
          icon: 'pv',
          power: mqttStore.pvPowerIndividual(id, 'textValue') as string,
          powerValue: mqttStore.pvPowerIndividual(id, 'value') as number,
          today: {
            exported: mqttStore.pvDailyExportedIndividual(
              id,
              'textValue',
            ) as string,
          },
          color: mqttStore.pvColor(id) || 'var(--q-pv-stroke)',
        });
      }
    });
    return pvSystems;
  });

  const individualConsumerData = computed((): DailyTotalsItem[] => {
    const consumers: DailyTotalsItem[] = [];

    mqttStore.consumerIds.forEach((id) => {
      const name = mqttStore.consumerName(id);
      if (name !== undefined) {
        consumers.push({
          id: `consumer-${id}`,
          title: name,
          level: 'secondary',
          icon: 'consumer',
          power: mqttStore.consumerPower(id, 'textValue') as string,
          powerValue: mqttStore.consumerPower(id, 'value') as number,
          today: {
            imported: mqttStore.consumerDailyImported(
              'textValue',
              id,
            ) as string,
          },
          color: mqttStore.consumerColor(id) || 'var(--q-consumer)',
        });
      }
    });
    return consumers;
  });

  const componentData = computed((): DailyTotalsItem[] => {
    const components: DailyTotalsItem[] = [];

    if (batteryConfigured.value) {
      let item: DailyTotalsItem = {
        id: 'battery',
        title: 'Speicher',
        level: 'primary',
        icon: 'battery',
      };
      item = {
        ...item,
        soc: mqttStore.batterySocTotal,
        power: mqttStore.batteryTotalPower('textValue') as string,
        powerValue: mqttStore.batteryTotalPower('value') as number,
        today: {
          imported: mqttStore.batteryDailyImportedTotal('textValue') as string,
          exported: mqttStore.batteryDailyExportedTotal('textValue') as string,
        },
        color: 'var(--q-battery-stroke)',
      };
      components.push(item);
    }

    if (pvConfigured.value) {
      components.push({
        id: 'pv',
        title: 'PV',
        level: 'primary',
        icon: 'pv',
        power: mqttStore.pvPowerTotal('textValue') as string,
        powerValue: mqttStore.pvPowerTotal('value') as number,
        today: { exported: mqttStore.pvDailyExported('textValue') as string },
        color: 'var(--q-pv-stroke)',
      });
    }

    if (showHomePower.value) {
      components.push({
        id: 'house',
        title: 'Haus',
        level: 'primary',
        icon: 'house',
        power: mqttStore.homePower('textValue') as string,
        powerValue: mqttStore.homePower('value') as number,
        today: { imported: mqttStore.homeDailyYield('textValue') as string },
        color: 'var(--q-home-stroke)',
      });
    }

    if (chargePointConfigured.value || chargePointSumPowerAvailable.value) {
      let item: DailyTotalsItem = {
        id: 'chargepoint',
        title: mqttStore.chargePointIds.length > 1 ? 'Ladepunkte' : 'Ladepunkt',
        level: 'primary',
        icon: 'chargepoint',
        color:
          mqttStore.chargePointIds.length === 1
            ? mqttStore.chargePointColor(mqttStore.chargePointIds[0]) ||
              'var(--q-charge-point-stroke)'
            : 'var(--q-charge-point-stroke)',
      };
      if (chargePointSumPowerAvailable.value) {
        item = {
          ...item,
          power: mqttStore.chargePointSumPower('textValue') as string,
          powerValue: mqttStore.chargePointSumPower('value') as number,
          today: {
            imported: mqttStore.chargePointDailyImported('textValue') as string,
            exported: mqttStore.chargePointDailyExported('textValue') as string,
          },
        };
        if (mqttStore.chargePointIds.length === 1) {
          item.color =
            mqttStore.chargePointColor(mqttStore.chargePointIds[0]) ||
            undefined;
        }
      }
      components.push(item);
    }
    if (consumerConfigured.value) {
      components.push({
        id: 'consumer',
        title: 'Verbraucher',
        level: 'primary',
        icon: 'consumer',
        power: mqttStore.consumerSumPower('textValue') as string,
        powerValue: mqttStore.consumerSumPower('value') as number,
        today: {
          imported: mqttStore.consumerDailyImported('textValue') as string,
        },
        color:
          mqttStore.consumerIds.length === 1
            ? mqttStore.consumerColor(mqttStore.consumerIds[0]) ||
              'var(--q-consumer)'
            : 'var(--q-consumer)',
      });
    }
    return components;
  });

  return {
    showGrid,
    gridData,
    secondaryCounterData,
    individualChargePointData,
    individualBatteryData,
    individualPvData,
    individualConsumerData,
    componentData,
    secondaryComponentsConfigured,
  };
};
