<script setup lang="ts">
import { useMqttStore } from 'src/stores/mqtt-store';
import { useQuasar } from 'quasar';
import { ref, computed, watch } from 'vue';
import type { SvgSize, FlowComponent } from './energy-flow-chart-models';
import type { ValueObject } from 'src/stores/mqtt-store-model';
import BatteryIcon from 'src/assets/icons/owbBattery_2.svg?component';
import GridIcon from 'src/assets/icons/owbGrid.svg?component';
import PvIcon from 'src/assets/icons/owbPV.svg?component';
import HouseIcon from 'src/assets/icons/owbHouse.svg?component';
import VehicleIcon from 'src/assets/icons/owbVehicle.svg?component';
import ChargePointIcon from 'src/assets/icons/owbChargePoint_2.svg?component';
import ConsumerIcon from 'src/assets/icons/owbConsumer.svg?component';

const mqttStore = useMqttStore();
const $q = useQuasar();

const svgSize = ref<SvgSize>({
  xMin: 0,
  xMax: 150,
  yMin: 0,
  yMax: 105,
  circleRadius: 10,
  strokeWidth: 0.5,
  textSize: 5,
  numRows: 4,
  numColumns: 3,
});

const BASE_CHART_WIDTH = 150;
const chartWidth = computed(() => {
  if ($q.screen.gt.md) return 170;
  if ($q.screen.gt.sm) return 160;
  return BASE_CHART_WIDTH;
});

watch(
  chartWidth,
  (newValue) => {
    svgSize.value.xMax = newValue;
  },
  { immediate: true },
);

const svgViewBox = computed(
  () =>
    `${svgSize.value.xMin} ${svgSize.value.yMin} ${svgSize.value.xMax} ${svgSize.value.yMax}`,
);

const svgIconWidth = computed(() => svgSize.value.circleRadius);

const svgIconHeight = computed(() => svgSize.value.circleRadius);

const svgFontSize = computed(() => `${svgSize.value.textSize}px`);

const absoluteValueObject = (valueObject: ValueObject): ValueObject => {
  // check for leading minus sign and remove it
  // energy direction is indicated by animated flow line
  // process object properties "textValue", "value" and "scaledValue" and return the modified valueObject
  let newValueObject = { ...valueObject } as ValueObject;
  if (newValueObject.textValue) {
    newValueObject.textValue = newValueObject.textValue.replace(/^-/, '');
  }
  if (newValueObject.value) {
    newValueObject.value = Math.abs(newValueObject.value);
  }
  if (newValueObject.scaledValue) {
    newValueObject.scaledValue = Math.abs(newValueObject.scaledValue);
  }
  return newValueObject;
};

const gridPower = computed(
  () => mqttStore.counterPower('object') as ValueObject,
);
const showGridPower = computed(() => {
  return gridPower.value.value !== undefined;
});
const gridConsumption = computed(() => Number(gridPower.value.value) > 0);
const gridFeedIn = computed(() => Number(gridPower.value.value) < 0);

const batteryPower = computed(
  () => mqttStore.batteryTotalPower('object') as ValueObject,
);
const batteryDischarging = computed(
  () => Number(mqttStore.batteryTotalPower('value')) < 0,
);
const batteryCharging = computed(
  () => Number(mqttStore.batteryTotalPower('value')) > 0,
);

const batterySoc = computed(() => Number(mqttStore.batterySocTotal) / 100);

const homePower = computed(() => mqttStore.homePower('object') as ValueObject);
const showHomePower = computed(() => {
  return homePower.value.value !== undefined;
});
const homeConsumption = computed(() => Number(homePower.value.value) > 0);
const homeProduction = computed(() => Number(homePower.value.value) < 0);

const consumerPower = computed(
  () => mqttStore.consumerSumPower('object') as ValueObject,
);
const showConsumerPower = computed(
  () => mqttStore.consumerIds.length > 0,
);

const pvPower = computed(() => mqttStore.pvPowerTotal('object') as ValueObject);
const pvProduction = computed(() => {
  const value = Number(pvPower.value.value);
  return value < 0;
});
const pvConsumption = computed(() => {
  const value = Number(pvPower.value.value);
  return value > 0;
});

const connectedChargePoints = computed(() => mqttStore.chargePointIds);

const chargePoint1Name = computed(
  () => mqttStore.chargePointName(connectedChargePoints.value[0]) || '---',
);
const chargePoint2Name = computed(
  () => mqttStore.chargePointName(connectedChargePoints.value[1]) || '---',
);
const chargePoint3Name = computed(
  () => mqttStore.chargePointName(connectedChargePoints.value[2]) || '---',
);

const chargePoint1Power = computed(() => {
  if (connectedChargePoints.value.length > 0) {
    return (
      (mqttStore.chargePointPower(
        connectedChargePoints.value[0],
        'object',
      ) as ValueObject) || ({ textValue: 'Loading...' } as ValueObject)
    );
  }
  return { textValue: 'N/A' } as ValueObject;
});

const chargePoint2Power = computed(() => {
  if (connectedChargePoints.value.length > 1) {
    return (
      (mqttStore.chargePointPower(
        connectedChargePoints.value[1],
        'object',
      ) as ValueObject) || ({ textValue: 'Loading...' } as ValueObject)
    );
  }
  return { textValue: 'N/A' } as ValueObject;
});

const chargePoint3Power = computed(() => {
  if (connectedChargePoints.value.length > 2) {
    return (
      (mqttStore.chargePointPower(
        connectedChargePoints.value[2],
        'object',
      ) as ValueObject) || ({ textValue: 'Loading...' } as ValueObject)
    );
  }
  return { textValue: 'N/A' } as ValueObject;
});

const chargePoint1Charging = computed(
  () => Number(chargePoint1Power.value.value) > 0,
);
const chargePoint1Discharging = computed(
  () => Number(chargePoint1Power.value.value) < 0,
);

const chargePoint2Charging = computed(
  () => Number(chargePoint2Power.value.value) > 0,
);
const chargePoint2Discharging = computed(
  () => Number(chargePoint2Power.value.value) < 0,
);

const chargePoint3Charging = computed(
  () => Number(chargePoint3Power.value.value) > 0,
);
const chargePoint3Discharging = computed(
  () => Number(chargePoint3Power.value.value) < 0,
);

///////////////////////// connected vehicle /////////////////////////

const translateChargeMode = (mode: string) => {
  switch (mode) {
    case 'instant_charging':
      return { label: 'Sofort' };
    case 'pv_charging':
      return { label: 'PV' };
    case 'scheduled_charging':
      return { label: 'Zielladen' };
    case 'time_charging':
      return { label: 'Zeitladen' };
    case 'eco_charging':
      return { label: 'Eco' };
    case 'stop':
      return { label: 'Stop' };
    default:
      return { label: 'Stop' };
  }
};

const chargePoint1VehicleConnected = computed(() =>
  mqttStore.chargePointPlugState(connectedChargePoints.value[0]),
);

const chargePoint1ConnectedVehicleChargeMode = computed(() => {
  const mode = mqttStore.chargePointConnectedVehicleChargeMode(
    connectedChargePoints.value[0],
  );
  return translateChargeMode(mode.value || '');
});

const chargePoint1ConnectedVehicle = computed(() => {
  const cpId = connectedChargePoints.value[0];
  return mqttStore.chargePointConnectedVehicleInfo(cpId).value || null;
});

const chargePoint1ConnectedVehicleSoc = computed(() =>
  mqttStore.chargePointConnectedVehicleSoc(connectedChargePoints.value[0]),
);

const chargePoint2VehicleConnected = computed(() => {
  if (connectedChargePoints.value.length > 1) {
    return mqttStore.chargePointPlugState(connectedChargePoints.value[1]);
  }
  return false;
});

const chargePoint2ConnectedVehicleChargeMode = computed(() => {
  const mode = mqttStore.chargePointConnectedVehicleChargeMode(
    connectedChargePoints.value[1],
  );
  return translateChargeMode(mode.value || '');
});

const chargePoint2ConnectedVehicle = computed(
  () =>
    mqttStore.chargePointConnectedVehicleInfo(connectedChargePoints.value[1])
      .value || null,
);

const chargePoint2ConnectedVehicleSoc = computed(() =>
  mqttStore.chargePointConnectedVehicleSoc(connectedChargePoints.value[1]),
);

const chargePoint3VehicleConnected = computed(() => {
  if (connectedChargePoints.value.length > 2) {
    return mqttStore.chargePointPlugState(connectedChargePoints.value[2]);
  }
  return false;
});

const chargePoint3ConnectedVehicleChargeMode = computed(() => {
  const mode = mqttStore.chargePointConnectedVehicleChargeMode(
    connectedChargePoints.value[2],
  );
  return translateChargeMode(mode.value || '');
});

const chargePoint3ConnectedVehicle = computed(
  () =>
    mqttStore.chargePointConnectedVehicleInfo(connectedChargePoints.value[2])
      .value || null,
);

const chargePoint3ConnectedVehicleSoc = computed(() =>
  mqttStore.chargePointConnectedVehicleSoc(connectedChargePoints.value[2]),
);

const chargePointSumPower = computed(
  () => mqttStore.chargePointSumPower('object') as ValueObject,
);

const chargePointSumDischarging = computed(
  () => Number(chargePointSumPower.value.value) < 0,
);
const chargePointSumCharging = computed(
  () => Number(chargePointSumPower.value.value) > 0,
);

///////////////////// Set animation speed //////////////////////////

const maxSystemPower = computed(() => {
  const powerValues = [
    Math.abs(Number(gridPower.value.value)),
    Math.abs(Number(homePower.value.value)),
    Math.abs(Number(consumerPower.value.value)),
    Math.abs(Number(pvPower.value.value)),
    Math.abs(Number(batteryPower.value.value)),
    Math.abs(Number(chargePoint1Power.value.value)),
    Math.abs(Number(chargePoint2Power.value.value)),
    Math.abs(Number(chargePoint3Power.value.value)),
    // Only take the sum into account if there are more than 3 charging points
    ...(connectedChargePoints.value.length > 3
      ? [Math.abs(Number(chargePointSumPower.value.value))]
      : []),
  ];
  const filteredPowerValues = powerValues.filter(
    (value) => !isNaN(value) && value !== undefined && value !== null,
  );
  if (filteredPowerValues.length === 0) return 1000;
  return Math.max(...filteredPowerValues);
});

function calcDuration(power: number, maxPower: number) {
  const minDuration = 3;
  const maxDuration = 10;
  const absPower = Math.abs(power || 0);
  if (absPower >= maxPower) return `${minDuration}s`;
  if (absPower > 0)
    return `${maxDuration - (maxDuration - minDuration) * (absPower / maxPower)}s`;
  return `${maxDuration}s`;
}

const animationDurations = computed(() => {
  const maxPower = maxSystemPower.value;
  return {
    grid: calcDuration(Number(gridPower.value.value), maxPower),
    home: calcDuration(Number(homePower.value.value), maxPower),
    consumer: calcDuration(Number(consumerPower.value.value), maxPower),
    pv: calcDuration(Number(pvPower.value.value), maxPower),
    battery: calcDuration(Number(batteryPower.value.value), maxPower),
    chargePoint1: calcDuration(Number(chargePoint1Power.value.value), maxPower),
    chargePoint2: calcDuration(Number(chargePoint2Power.value.value), maxPower),
    chargePoint3: calcDuration(Number(chargePoint3Power.value.value), maxPower),
    chargePointSum: calcDuration(
      Number(chargePointSumPower.value.value),
      maxPower,
    ),
    vehicle1: calcDuration(Number(chargePoint1Power.value.value), maxPower),
    vehicle2: calcDuration(Number(chargePoint2Power.value.value), maxPower),
    vehicle3: calcDuration(Number(chargePoint3Power.value.value), maxPower),
  };
});

///////////////////////// Diagram components /////////////////////////

const svgComponents = computed((): FlowComponent[] => {
  const components: FlowComponent[] = [];

  if (showGridPower.value) {
    components.push({
      id: 'grid',
      class: {
        base: 'grid',
        valueLabelColor: gridFeedIn.value
          ? 'var(--q-pv-stroke)'
          : gridConsumption.value
            ? 'var(--q-grid-stroke)'
            : 'var(--q-text)',
        animated: gridConsumption.value,
        animatedReverse: gridFeedIn.value,
      },
      position: { row: 0, column: 0 },
      label: ['EVU', absoluteValueObject(gridPower.value).textValue],
      powerValue: Number(gridPower.value.value),
      iconComponent: GridIcon,
      iconColor: 'var(--q-grid-stroke)',
    });
  }

  if (showHomePower.value) {
    components.push({
      id: 'home',
      class: {
        base: 'home',
        animated: homeProduction.value,
        animatedReverse: homeConsumption.value,
      },
      position: { row: 0, column: 2 },
      label: ['Haus', absoluteValueObject(homePower.value).textValue],
      powerValue: Number(homePower.value.value),
      iconComponent: HouseIcon,
      iconColor: 'var(--q-home-stroke)',
    });
  }

  if (showConsumerPower.value) {
    components.push({
      id: 'consumer',
      class: {
        base: 'consumer',
        valueLabelColor: 'var(--q-consumer)',
        animatedReverse: Number(consumerPower.value.value) > 0,
      },
      position: { row: 0, column: 1 },
      label: ['Verbraucher', absoluteValueObject(consumerPower.value).textValue],
      powerValue: Number(consumerPower.value.value),
      iconComponent: ConsumerIcon,
      iconColor: 'var(--q-consumer)',
    });
  }

  if (mqttStore.pvConfigured) {
    components.push({
      id: 'pv',
      class: {
        base: 'pv',
        animated: pvProduction.value,
        animatedReverse: pvConsumption.value,
      },
      position: { row: 1, column: 0 },
      label: ['PV', absoluteValueObject(pvPower.value).textValue],
      powerValue: Number(pvPower.value.value),
      iconComponent: PvIcon,
      iconColor: 'var(--q-pv-stroke)',
    });
  }

  if (mqttStore.batteryConfigured) {
    components.push({
      id: 'battery',
      class: {
        base: 'battery',
        animated: batteryDischarging.value,
        animatedReverse: batteryCharging.value,
      },
      position: { row: 1, column: 2 },
      label: ['Speicher', absoluteValueObject(batteryPower.value).textValue],
      powerValue: Number(batteryPower.value.value),
      soc: batterySoc.value,
      iconComponent: BatteryIcon,
      iconColor: 'var(--q-battery-stroke)',
    });
  }

  if (connectedChargePoints.value.length > 0) {
    if (connectedChargePoints.value.length <= 3) {
      // add charge point 1 component
      components.push({
        id: 'charge-point-1',
        class: {
          base: 'charge-point',
          animationId: 'charge-point-1',
          animated: chargePoint1Discharging.value,
          animatedReverse: chargePoint1Charging.value,
        },
        position: {
          row: 2,
          column: connectedChargePoints.value.length > 1 ? 0 : 1,
        },
        label: [
          chargePoint1Name.value,
          absoluteValueObject(chargePoint1Power.value).textValue,
        ],
        powerValue: Number(chargePoint1Power.value.value),
        iconComponent: ChargePointIcon,
        iconColor:
          mqttStore.chargePointColor(connectedChargePoints.value[0]) ||
          'var(--q-charge-point-stroke)',
      });

      if (chargePoint1VehicleConnected.value) {
        // add vehicle 1 component
        components.push({
          id: 'vehicle-1',
          class: {
            base: 'vehicle',
            animationId: 'vehicle-1',
            animated: chargePoint1Discharging.value,
            animatedReverse: chargePoint1Charging.value,
          },
          position: {
            row: 3,
            column: connectedChargePoints.value.length > 1 ? 0 : 1,
          },
          label: [
            chargePoint1ConnectedVehicle.value?.name || '---',
            chargePoint1ConnectedVehicleChargeMode.value.label || '---',
          ],
          soc: (chargePoint1ConnectedVehicleSoc.value.value?.soc || 0) / 100,
          iconComponent: VehicleIcon,
          iconColor: chargePoint1ConnectedVehicle.value?.id
            ? mqttStore.vehicleColor(chargePoint1ConnectedVehicle.value?.id) ||
              'var(--q-vehicle-stroke)'
            : 'var(--q-vehicle-stroke)',
          powerValue: Number(chargePoint1Power.value.value),
        });
      }

      if (connectedChargePoints.value.length > 1) {
        // add charge point 2 component
        components.push({
          id: 'charge-point-2',
          class: {
            base: 'charge-point',
            animationId: 'charge-point-2',
            animated: chargePoint2Discharging.value,
            animatedReverse: chargePoint2Charging.value,
          },
          position: {
            row: 2,
            column: connectedChargePoints.value.length > 2 ? 1 : 2,
          },
          label: [
            chargePoint2Name.value,
            absoluteValueObject(chargePoint2Power.value).textValue,
          ],
          powerValue: Number(chargePoint2Power.value.value),
          iconComponent: ChargePointIcon,
          iconColor:
            mqttStore.chargePointColor(connectedChargePoints.value[1]) ||
            'var(--q-charge-point-stroke)',
        });
      }

      if (chargePoint2VehicleConnected.value) {
        // add vehicle 2 component
        components.push({
          id: 'vehicle-2',
          class: {
            base: 'vehicle',
            animationId: 'vehicle-2',
            animated: chargePoint2Discharging.value,
            animatedReverse: chargePoint2Charging.value,
          },
          position: {
            row: 3,
            column: connectedChargePoints.value.length > 2 ? 1 : 2,
          },
          label: [
            chargePoint2ConnectedVehicle.value?.name || '---',
            chargePoint2ConnectedVehicleChargeMode.value.label || '---',
          ],
          soc: (chargePoint2ConnectedVehicleSoc.value.value?.soc || 0) / 100,
          iconComponent: VehicleIcon,
          iconColor: chargePoint2ConnectedVehicle.value?.id
            ? mqttStore.vehicleColor(chargePoint2ConnectedVehicle.value?.id) ||
              'var(--q-vehicle-stroke)'
            : 'var(--q-vehicle-stroke)',
          powerValue: Number(chargePoint2Power.value.value),
        });
      }

      if (connectedChargePoints.value.length > 2) {
        // add charge point 3 component
        components.push({
          id: 'charge-point-3',
          class: {
            base: 'charge-point',
            animationId: 'charge-point-3',
            animated: chargePoint3Discharging.value,
            animatedReverse: chargePoint3Charging.value,
          },
          position: { row: 2, column: 2 },
          label: [
            chargePoint3Name.value,
            absoluteValueObject(chargePoint3Power.value).textValue,
          ],
          powerValue: Number(chargePoint3Power.value.value),
          iconComponent: ChargePointIcon,
          iconColor:
            mqttStore.chargePointColor(connectedChargePoints.value[2]) ||
            'var(--q-charge-point-stroke)',
        });
      }

      if (chargePoint3VehicleConnected.value) {
        // add vehicle 3 component
        components.push({
          id: 'vehicle-3',
          class: {
            base: 'vehicle',
            animationId: 'vehicle-3',
            animated: chargePoint3Discharging.value,
            animatedReverse: chargePoint3Charging.value,
          },
          position: {
            row: 3,
            column: 2,
          },
          label: [
            chargePoint3ConnectedVehicle.value?.name || '---',
            chargePoint3ConnectedVehicleChargeMode.value.label || '---',
          ],
          soc: (chargePoint3ConnectedVehicleSoc.value.value?.soc || 0) / 100,
          iconComponent: VehicleIcon,
          iconColor: chargePoint3ConnectedVehicle.value?.id
            ? mqttStore.vehicleColor(chargePoint3ConnectedVehicle.value?.id) ||
              'var(--q-vehicle-stroke)'
            : 'var(--q-vehicle-stroke)',
          powerValue: Number(chargePoint3Power.value.value),
        });
      }
    } else if (chargePointSumPower.value !== undefined) {
      // add charge point sum component
      components.push({
        id: 'charge-point-sum',
        class: {
          base: 'charge-point',
          animationId: 'charge-point-sum',
          animated: chargePointSumDischarging.value,
          animatedReverse: chargePointSumCharging.value,
        },
        position: { row: 2, column: 1 },
        label: [
          'Ladepunkte',
          absoluteValueObject(chargePointSumPower.value).textValue,
        ],
        powerValue: Number(chargePointSumPower.value.value),
        iconComponent: ChargePointIcon,
        iconColor: 'var(--q-charge-point-stroke)',
      });
    }
  }
  return components;
});

const calculatedRows = computed(() => {
  if (connectedChargePoints.value?.length > 0) {
    return connectedChargePoints.value.length > 3 ? 3 : 4;
  }
  return 3;
});

watch(
  calculatedRows,
  (newValue) => {
    svgSize.value.numRows = newValue;
  },
  { immediate: true },
);

const calcRowY = (row: number): number => {
  const yMin =
    svgSize.value.yMin + svgSize.value.strokeWidth + svgSize.value.circleRadius;
  const yMax =
    svgSize.value.yMax - svgSize.value.strokeWidth - svgSize.value.circleRadius;
  const yRange = yMax - yMin;
  return row * (yRange / (svgSize.value.numRows - 1)) + yMin;
};

const calcColumnX = (column: number): number => {
  const xMin =
    svgSize.value.xMin + svgSize.value.strokeWidth + svgRectWidth.value / 2;
  const xMax =
    svgSize.value.xMax - svgSize.value.strokeWidth - svgRectWidth.value / 2;
  const xRange = xMax - xMin;
  return column * (xRange / (svgSize.value.numColumns - 1)) + xMin;
};

const calcFlowLineAnchorX = (column: number): number => {
  const columnX = calcColumnX(column);
  if (column < (svgSize.value.numColumns - 1) / 2) {
    return columnX + svgRectWidth.value / 2 - svgSize.value.circleRadius;
  } else if (column > (svgSize.value.numColumns - 1) / 2) {
    return columnX - svgRectWidth.value / 2 + svgSize.value.circleRadius;
  }
  return columnX;
};

const calcFlowPath = (component: FlowComponent): string => {
  const x1 = calcFlowLineAnchorX(component.position.column);
  const y1 = calcRowY(component.position.row);
  if (component.class.base === 'vehicle') {
    return `M ${x1}, ${y1} ${x1}, ${calcRowY(component.position.row - 1)}`;
  }
  return `M ${x1}, ${y1} ${calcColumnX(1)}, ${calcRowY(1)}`;
};

const calcSvgElementBoundingBox = (elementId: string) => {
  const element = document.getElementById(elementId);
  if (element == undefined || !(element instanceof SVGGraphicsElement)) {
    return { x: 0, y: 0, width: 0, height: 0 };
  }
  const boundingBox = element.getBBox();
  return {
    x: boundingBox.x,
    y: boundingBox.y,
    width: boundingBox.width,
    height: boundingBox.height,
  };
};

const beginAnimation = (elementId: string) => {
  const element = document.querySelector(`#${elementId}`) as SVGAnimateElement;
  if (element) {
    element.beginElement();
  }
};

const svgRectWidth = computed(
  () =>
    (BASE_CHART_WIDTH -
      svgSize.value.xMin -
      svgSize.value.strokeWidth -
      svgSize.value.numColumns) /
    svgSize.value.numColumns,
);

const labelClipPath = computed(() => {
  const cr = svgSize.value.circleRadius;
  const iconCenter = cr - svgRectWidth.value / 2; // icon circle center x
  const curveStart = svgRectWidth.value / 2 - cr; // where the right curve begins
  const top = -cr;
  const bottom = cr;
  return (
    `M ${iconCenter} ${top} ` +
    `L ${curveStart} ${top} ` +
    `A ${cr} ${cr} 0 0 1 ${curveStart} ${bottom} ` +
    `L ${iconCenter} ${bottom} ` +
    `A ${cr} ${cr} 0 0 0 ${iconCenter} ${top} ` +
    'Z'
  );
});
</script>

<template>
  <div class="svg-container">
    <svg
      :viewBox="svgViewBox"
      version="1.1"
      xmlns="http://www.w3.org/2000/svg"
      xmlns:svg="http://www.w3.org/2000/svg"
    >
      <defs>
        <filter
          id="flow-box-shadow"
          x="-50%"
          y="-50%"
          width="200%"
          height="200%"
          filterUnits="objectBoundingBox"
        >
          <feDropShadow dx="0" dy="0" stdDeviation="1" />
        </filter>
      </defs>

      <g id="layer1" style="display: inline">
        <g v-for="component in svgComponents" :key="component.id">
          <!-- static background line -->
          <path
            class="flow-base"
            :class="{
              animated: component.class.animated,
              animatedReverse: component.class.animatedReverse,
            }"
            :d="calcFlowPath(component)"
          />
          <!-- glowing flow overlay -->
          <path
            :id="`flow-path-${component.id}`"
            class="flow-animated"
            :class="[
              component.class.base,
              component.class.animationId,
              { animated: component.class.animated },
              { animatedReverse: component.class.animatedReverse },
            ]"
            :d="calcFlowPath(component)"
          />
        </g>
      </g>

      <g id="layer2" style="display: inline">
        <!-- center dot -->
        <circle
          id="center"
          :cx="calcColumnX(1)"
          :cy="calcRowY(1)"
          :r="svgSize.circleRadius / 3"
          filter="url(#flow-box-shadow)"
        />

        <!-- components -->
        <g
          v-for="component in svgComponents"
          :key="component.id"
          :class="component.class.base"
          :transform="`translate(${calcColumnX(component.position.column)}, ${calcRowY(component.position.row)})`"
          @click="beginAnimation(`animate-label-${component.id}`)"
        >
          <defs>
            <clipPath
              v-if="component.soc !== undefined"
              :id="`clip-soc-${component.id}`"
            >
              <rect
                :x="-svgSize.circleRadius - svgSize.strokeWidth"
                :y="(svgSize.circleRadius - 1) * (1 - 2 * component.soc)"
                :width="(svgSize.circleRadius + svgSize.strokeWidth) * 2"
                :height="(svgSize.circleRadius - 1) * 2 * component.soc"
              />
            </clipPath>
            <clipPath :id="`clip-label-${component.id}`">
              <path :d="labelClipPath" />
            </clipPath>
            <linearGradient
              :id="`gradient-soc-${component.id}`"
              x1="0%"
              y1="0%"
              x2="0%"
              y2="100%"
            >
              <stop
                offset="0%"
                stop-color="var(--soc-color)"
                stop-opacity="25%"
              />
              <stop
                offset="100%"
                stop-color="var(--soc-color)"
                stop-opacity="50%"
              />
            </linearGradient>
          </defs>
          <rect
            :x="-svgRectWidth / 2"
            :y="-svgSize.circleRadius"
            :width="svgRectWidth"
            :height="svgSize.circleRadius * 2"
            :rx="svgSize.circleRadius"
            :ry="svgSize.circleRadius"
            filter="url(#flow-box-shadow)"
          />
          <text :clip-path="`url(#clip-label-${component.id})`">
            <tspan
              :id="`label-${component.id}`"
              text-anchor="start"
              :x="
                -svgRectWidth / 2 +
                2 * svgSize.circleRadius +
                svgSize.strokeWidth
              "
              :y="-svgSize.textSize / 2"
            >
              <animate
                v-if="
                  calcSvgElementBoundingBox(`label-${component.id}`).width >
                  svgRectWidth -
                    2 * svgSize.circleRadius -
                    2 * svgSize.strokeWidth
                "
                :id="`animate-label-${component.id}`"
                xmlns="http://www.w3.org/2000/svg"
                attributeName="x"
                dur="5s"
                :values="
                  '0; ' +
                  (-calcSvgElementBoundingBox(`label-${component.id}`).width +
                    svgRectWidth -
                    2.5 * svgSize.circleRadius -
                    2 * svgSize.strokeWidth) +
                  '; 0;'
                "
                repeatCount="0"
                additive="sum"
              />
              {{ component.label[0] }}
            </tspan>
            <tspan
              :id="`value-${component.id}`"
              :style="{
                fill: component.class.valueLabelColor ?? component.iconColor,
              }"
              text-anchor="end"
              :x="2 * svgSize.circleRadius + svgSize.strokeWidth"
              :y="svgSize.textSize"
            >
              {{ component.label[1] }}
            </tspan>
          </text>
          <g
            :transform="`translate(${svgSize.circleRadius - svgRectWidth / 2}, 0)`"
          >
            <circle
              cx="0"
              cy="0"
              :r="svgSize.circleRadius - 1"
              filter="url(#flow-box-shadow)"
            />
            <!-- SoC fill: radius must match the clip-soc reference above so the
                 fill level is accurate, and the background circle below so it
                 reaches the inner edge of the border instead of leaving a rim -->
            <circle
              v-if="component.soc !== undefined"
              :class="{ soc: component.soc !== undefined }"
              cx="0"
              cy="0"
              :r="svgSize.circleRadius - 1"
              :clip-path="`url(#clip-soc-${component.id})`"
              :fill="`url(#gradient-soc-${component.id})`"
            />
            <g
              :transform="`translate(${-svgIconWidth / 2}, ${-svgIconHeight / 2})`"
            >
              <component
                :is="component.iconComponent"
                :width="svgIconWidth"
                :height="svgIconHeight"
                :style="{ color: component.iconColor }"
              />
            </g>
          </g>
        </g>
      </g>
    </svg>
  </div>
</template>

<style scoped>
.svg-container {
  display: flex;
  flex-direction: column;
  align-items: center;
  width: 100%;
  height: 100%;
  user-select: none;
}

svg {
  width: 100%;
  height: 100%;
  object-fit: contain;
}

.flow-base {
  fill: none;
  stroke: var(--q-secondary);
  stroke-width: 0.75;
  stroke-linecap: round;
  stroke-linejoin: round;
  transition: stroke 0.5s;
}

/* slightly darker solid line beneath an active flow */
.flow-base.animated,
.flow-base.animatedReverse {
  stroke: var(--q-grey);
}

/* overlay stays hidden until energy is flowing */
.flow-animated {
  fill: none;
  stroke: none;
}

/* Animated energy flow: glowing dots traveling along the line */
.flow-animated.animated,
.flow-animated.animatedReverse {
  stroke: currentColor;
  stroke-width: 1.8;
  stroke-linecap: round;
  stroke-dasharray: 2 50;
  animation-timing-function: linear;
  animation-iteration-count: infinite;
  filter: drop-shadow(0 0 2px currentColor) drop-shadow(0 0 6px currentColor);
}

.flow-animated.animated {
  animation-name: energyFlow;
}
.flow-animated.animatedReverse {
  animation-name: energyFlowReverse;
}

path.animated.grid {
  color: var(--q-negative);
  animation-duration: v-bind('animationDurations.grid');
}
path.animatedReverse.grid {
  color: var(--q-pv-stroke);
  animation-duration: v-bind('animationDurations.grid');
}

path.animated.home,
path.animatedReverse.home {
  color: var(--q-home-stroke);
  animation-duration: v-bind('animationDurations.home');
}

path.animatedReverse.consumer {
  color: var(--q-consumer);
  animation-duration: v-bind('animationDurations.consumer');
}

path.animated.pv,
path.animatedReverse.pv {
  color: var(--q-pv-stroke);
  animation-duration: v-bind('animationDurations.pv');
}

path.animated.battery,
path.animatedReverse.battery {
  color: var(--q-battery-stroke);
  animation-duration: v-bind('animationDurations.battery');
}

path.animated.charge-point-1,
path.animatedReverse.charge-point-1 {
  color: var(--q-charge-point-stroke);
  animation-duration: v-bind('animationDurations.chargePoint1');
}
path.animated.charge-point-2,
path.animatedReverse.charge-point-2 {
  color: var(--q-charge-point-stroke);
  animation-duration: v-bind('animationDurations.chargePoint2');
}
path.animated.charge-point-3,
path.animatedReverse.charge-point-3 {
  color: var(--q-charge-point-stroke);
  animation-duration: v-bind('animationDurations.chargePoint3');
}
path.animated.charge-point-sum,
path.animatedReverse.charge-point-sum {
  color: var(--q-charge-point-stroke);
  animation-duration: v-bind('animationDurations.chargePointSum');
}

path.animated.vehicle-1,
path.animatedReverse.vehicle-1 {
  color: var(--q-vehicle-stroke);
  animation-duration: v-bind('animationDurations.vehicle1');
}
path.animated.vehicle-2,
path.animatedReverse.vehicle-2 {
  color: var(--q-vehicle-stroke);
  animation-duration: v-bind('animationDurations.vehicle2');
}
path.animated.vehicle-3,
path.animatedReverse.vehicle-3 {
  color: var(--q-vehicle-stroke);
  animation-duration: v-bind('animationDurations.vehicle3');
}

@keyframes energyFlow {
  0% {
    stroke-dashoffset: 0;
  }
  100% {
    stroke-dashoffset: -200;
  }
}
@keyframes energyFlowReverse {
  0% {
    stroke-dashoffset: -200;
  }
  100% {
    stroke-dashoffset: 0;
  }
}

circle {
  fill-opacity: 1;
}

circle:not(.soc) {
  fill: var(--q-card-background);
}

rect {
  fill: var(--q-card-background);
}

/* Drop shadow by way of feDropShadow for browser compatibility (safari webkit) */
feDropShadow {
  flood-color: var(--q-shadow);
  flood-opacity: 1;
}

text {
  font-size: v-bind(svgFontSize);
  line-height: 1.25;
  font-family: 'Roboto', sans-serif;
  fill: var(--q-text);
  fill-opacity: 1;
}

.battery {
  --soc-color: var(--q-battery-stroke);
}

.vehicle {
  --soc-color: var(--q-vehicle-fill);
}

use {
  fill: currentColor;
}
</style>
