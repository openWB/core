<script setup lang="ts">
import { useMqttStore } from 'src/stores/mqtt-store';
import { ref, computed, watch } from 'vue';
import type { SvgSize, FlowComponent } from './energy-flow-chart-models';
import type { ValueObject } from 'src/stores/mqtt-store-model';

const mqttStore = useMqttStore();

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

const svgViewBox = computed(
  () =>
    `${svgSize.value.xMin} ${svgSize.value.yMin} ${svgSize.value.xMax} ${svgSize.value.yMax}`,
);

const svgStrokeWidth = computed(() => svgSize.value.strokeWidth);

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
  () => mqttStore.getCounterPower('object') as ValueObject,
);
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

const homePower = computed(
  () => mqttStore.getHomePower('object') as ValueObject,
);
const homeConsumption = computed(() => Number(homePower.value.value) > 0);
const homeProduction = computed(() => Number(homePower.value.value) < 0);

const pvPower = computed(() => mqttStore.getPvPower('object') as ValueObject);
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
  if (connectedChargePoints.value.length > 0) {
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
  if (connectedChargePoints.value.length > 0) {
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
      return { label: 'Sofort', class: 'danger' };
    case 'pv_charging':
      return { label: 'PV', class: 'success' };
    case 'scheduled_charging':
      return { label: 'Zielladen', class: 'primary' };
    case 'time_charging':
      return { label: 'Zeitladen', class: 'warning' };
    case 'eco_charging':
      return { label: 'Eco', class: 'secondary' };
    case 'stop':
      return { label: 'Stop', class: 'dark' };
    default:
      return { label: 'Stop', class: 'dark' };
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

const chargePoint1ConnectedVehicleName = computed(
  () =>
    mqttStore.chargePointConnectedVehicleInfo(connectedChargePoints.value[0])
      .value?.name || '---',
);

const chargePoint1ConnectedVehicleSoc = computed(() =>
  mqttStore.chargePointConnectedVehicleSoc(connectedChargePoints.value[0]),
);

const chargePoint2VehicleConnected = computed(() =>
  mqttStore.chargePointPlugState(connectedChargePoints.value[1]),
);

const chargePoint2ConnectedVehicleChargeMode = computed(() => {
  const mode = mqttStore.chargePointConnectedVehicleChargeMode(
    connectedChargePoints.value[1],
  );
  return translateChargeMode(mode.value || '');
});

const chargePoint2ConnectedVehicleName = computed(
  () =>
    mqttStore.chargePointConnectedVehicleInfo(connectedChargePoints.value[1])
      .value?.name || '---',
);

const chargePoint2ConnectedVehicleSoc = computed(() =>
  mqttStore.chargePointConnectedVehicleSoc(connectedChargePoints.value[1]),
);

const chargePoint3VehicleConnected = computed(() =>
  mqttStore.chargePointPlugState(connectedChargePoints.value[2]),
);

const chargePoint3ConnectedVehicleChargeMode = computed(() => {
  const mode = mqttStore.chargePointConnectedVehicleChargeMode(
    connectedChargePoints.value[2],
  );
  return translateChargeMode(mode.value || '');
});

const chargePoint3ConnectedVehicleName = computed(
  () =>
    mqttStore.chargePointConnectedVehicleInfo(connectedChargePoints.value[2])
      .value?.name || '---',
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
  const minDuration = 0.4;
  const maxDuration = 4.0;
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

  components.push({
    id: 'grid',
    class: {
      base: 'grid',
      valueLabel: gridFeedIn.value
        ? 'fill-success'
        : gridConsumption.value
          ? 'fill-danger'
          : '',
      animated: gridConsumption.value,
      animatedReverse: gridFeedIn.value,
    },
    position: { row: 0, column: 0 },
    label: ['EVU', absoluteValueObject(gridPower.value).textValue],
    powerValue: Number(gridPower.value.value),
    icon: 'icons/owbGrid.svg',
  });

  components.push({
    id: 'home',
    class: {
      base: 'home',
      valueLabel: '',
      animated: homeProduction.value,
      animatedReverse: homeConsumption.value,
    },
    position: { row: 0, column: 2 },
    label: ['Haus', absoluteValueObject(homePower.value).textValue],
    powerValue: Number(homePower.value.value),
    icon: 'icons/owbHouse.svg',
  });

  if (mqttStore.getPvConfigured) {
    components.push({
      id: 'pv',
      class: {
        base: 'pv',
        valueLabel: 'fill-success',
        animated: pvProduction.value,
        animatedReverse: pvConsumption.value,
      },
      position: { row: 1, column: 0 },
      label: ['PV', absoluteValueObject(pvPower.value).textValue],
      powerValue: Number(pvPower.value.value),
      icon: 'icons/owbPV.svg',
    });
  }

  if (mqttStore.batteryConfigured) {
    components.push({
      id: 'battery',
      class: {
        base: 'battery',
        valueLabel: '',
        animated: batteryDischarging.value,
        animatedReverse: batteryCharging.value,
      },
      position: { row: 1, column: 2 },
      label: ['Speicher', absoluteValueObject(batteryPower.value).textValue],
      powerValue: Number(batteryPower.value.value),
      soc: batterySoc.value,
      icon: 'icons/owbBattery.svg',
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
          valueLabel: '',
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
        icon: 'icons/owbChargePoint.svg',
      });

      if (chargePoint1VehicleConnected.value) {
        // add vehicle 1 component
        components.push({
          id: 'vehicle-1',
          class: {
            base: 'vehicle',
            animationId: 'vehicle-1',
            valueLabel:
              'fill-' + chargePoint1ConnectedVehicleChargeMode.value.class,
            animated: chargePoint1Discharging.value,
            animatedReverse: chargePoint1Charging.value,
          },
          position: {
            row: 3,
            column: connectedChargePoints.value.length > 1 ? 0 : 1,
          },
          label: [
            chargePoint1ConnectedVehicleName.value || '---',
            chargePoint1ConnectedVehicleChargeMode.value.label || '---',
          ],
          soc: (chargePoint1ConnectedVehicleSoc.value.value?.soc || 0) / 100,
          icon: 'icons/owbVehicle.svg',
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
            valueLabel: '',
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
          icon: 'icons/owbChargePoint.svg',
        });
      }

      if (chargePoint2VehicleConnected.value) {
        // add vehicle 2 component
        components.push({
          id: 'vehicle-2',
          class: {
            base: 'vehicle',
            animationId: 'vehicle-2',
            valueLabel:
              'fill-' + chargePoint2ConnectedVehicleChargeMode.value.class,
            animated: chargePoint2Discharging.value,
            animatedReverse: chargePoint2Charging.value,
          },
          position: {
            row: 3,
            column: connectedChargePoints.value.length > 2 ? 1 : 2,
          },
          label: [
            chargePoint2ConnectedVehicleName.value || '---',
            chargePoint2ConnectedVehicleChargeMode.value.label || '---',
          ],
          soc: (chargePoint2ConnectedVehicleSoc.value.value?.soc || 0) / 100,
          icon: 'icons/owbVehicle.svg',
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
            valueLabel: '',
            animated: chargePoint3Discharging.value,
            animatedReverse: chargePoint3Charging.value,
          },
          position: { row: 2, column: 2 },
          label: [
            chargePoint3Name.value,
            absoluteValueObject(chargePoint3Power.value).textValue,
          ],
          powerValue: Number(chargePoint3Power.value.value),
          icon: 'icons/owbChargePoint.svg',
        });
      }

      if (chargePoint3VehicleConnected.value) {
        // add vehicle 3 component
        components.push({
          id: 'vehicle-3',
          class: {
            base: 'vehicle',
            animationId: 'vehicle-3',
            valueLabel:
              'fill-' + chargePoint3ConnectedVehicleChargeMode.value.class,
            animated: chargePoint3Discharging.value,
            animatedReverse: chargePoint3Charging.value,
          },
          position: {
            row: 3,
            column: 2,
          },
          label: [
            chargePoint3ConnectedVehicleName.value || '---',
            chargePoint3ConnectedVehicleChargeMode.value.label || '---',
          ],
          soc: (chargePoint3ConnectedVehicleSoc.value.value?.soc || 0) / 100,
          icon: 'icons/owbVehicle.svg',
          powerValue: Number(chargePoint3Power.value.value),
        });
      }
    } else {
      // add charge point sum component
      components.push({
        id: 'charge-point-sum',
        class: {
          base: 'charge-point',
          animationId: 'charge-point-sum',
          valueLabel: '',
          animated: chargePointSumDischarging.value,
          animatedReverse: chargePointSumCharging.value,
        },
        position: { row: 2, column: 1 },
        label: [
          'Ladepunkte',
          absoluteValueObject(chargePointSumPower.value).textValue,
        ],
        powerValue: Number(chargePointSumPower.value.value),
        icon: 'icons/owbChargePoint.svg',
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
    (svgSize.value.xMax -
      svgSize.value.xMin -
      svgSize.value.strokeWidth -
      svgSize.value.numColumns) /
    svgSize.value.numColumns,
);
</script>

<template>
  <div class="svg-container">
    <svg
      :viewBox="svgViewBox"
      version="1.1"
      xmlns="http://www.w3.org/2000/svg"
      xmlns:svg="http://www.w3.org/2000/svg"
    >
      <g id="layer1" style="display: inline">
        <path
          v-for="component in svgComponents"
          :key="component.id"
          :id="`flow-path-${component.id}`"
          :class="[
            component.class.base,
            component.class.animationId,
            { animated: component.class.animated },
            { animatedReverse: component.class.animatedReverse },
          ]"
          :d="
            component.class.base !== 'vehicle'
              ? `M ${calcFlowLineAnchorX(component.position.column)}, ` +
                `${calcRowY(component.position.row)} ${calcColumnX(1)}, ${calcRowY(1)}`
              : `M ${calcFlowLineAnchorX(component.position.column)}, ` +
                `${calcRowY(component.position.row)} ${calcFlowLineAnchorX(component.position.column)}, ${calcRowY(component.position.row - 1)}`
          "
        />
      </g>

      <g id="layer2" style="display: inline">
        <!-- center dot -->
        <circle
          id="center"
          :cx="calcColumnX(1)"
          :cy="calcRowY(1)"
          :r="svgSize.circleRadius / 3"
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
            <clipPath v-if="component.soc" :id="`clip-soc-${component.id}`">
              <rect
                :x="-svgSize.circleRadius - svgSize.strokeWidth"
                :y="
                  (svgSize.circleRadius + svgSize.strokeWidth) *
                  (1 - 2 * component.soc)
                "
                :width="(svgSize.circleRadius + svgSize.strokeWidth) * 2"
                :height="
                  (svgSize.circleRadius + svgSize.strokeWidth) *
                  2 *
                  component.soc
                "
              />
            </clipPath>
            <clipPath :id="`clip-label-${component.id}`">
              <rect
                :x="-svgRectWidth / 2"
                :y="-svgSize.circleRadius"
                :width="svgRectWidth"
                :height="svgSize.circleRadius * 2"
                :rx="svgSize.circleRadius"
                :ry="svgSize.circleRadius"
              />
            </clipPath>
          </defs>
          <rect
            :x="-svgRectWidth / 2"
            :y="-svgSize.circleRadius"
            :width="svgRectWidth"
            :height="svgSize.circleRadius * 2"
            :rx="svgSize.circleRadius"
            :ry="svgSize.circleRadius"
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
              :class="component.class.valueLabel"
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
              :r="svgSize.circleRadius"
              class="background-circle"
            />
            <circle
              cx="0"
              cy="0"
              :r="svgSize.circleRadius"
              :class="{ soc: component.soc }"
            />
            <circle
              v-if="component.soc"
              cx="0"
              cy="0"
              :r="svgSize.circleRadius"
              :clip-path="`url(#clip-soc-${component.id})`"
            />

            <image
              :href="component.icon"
              :x="-svgIconWidth / 2"
              :y="-svgIconHeight / 2"
              :height="svgIconHeight"
              :width="svgIconWidth"
            />
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

path {
  fill: none;
  fill-rule: evenodd;
  stroke: rgb(64, 64, 64);
  stroke-width: 0.75;
  stroke-linecap: butt;
  stroke-linejoin: miter;
  stroke-miterlimit: 4;
  transition: stroke 0.5s;
}

/* Basis for all animated lines */
path.animated {
  animation-name: dash;
  animation-timing-function: linear;
  animation-iteration-count: infinite;
  stroke-dasharray: 5;
}
path.animatedReverse {
  animation-name: dashReverse;
  animation-timing-function: linear;
  animation-iteration-count: infinite;
  stroke-dasharray: 5;
}

path.animated.grid {
  stroke: var(--q-negative);
  animation-duration: v-bind('animationDurations.grid');
}
path.animatedReverse.grid {
  stroke: var(--q-positive);
  animation-duration: v-bind('animationDurations.grid');
}

path.animated.home,
path.animatedReverse.home {
  stroke: var(--q-home-stroke);
  animation-duration: v-bind('animationDurations.home');
}

path.animated.pv,
path.animatedReverse.pv {
  stroke: var(--q-positive);
  animation-duration: v-bind('animationDurations.pv');
}

path.animated.battery,
path.animatedReverse.battery {
  stroke: var(--q-battery-stroke);
  animation-duration: v-bind('animationDurations.battery');
}

path.animated.charge-point-1,
path.animatedReverse.charge-point-1 {
  stroke: var(--q-charge-point-stroke);
  animation-duration: v-bind('animationDurations.chargePoint1');
}
path.animated.charge-point-2,
path.animatedReverse.charge-point-2 {
  stroke: var(--q-charge-point-stroke);
  animation-duration: v-bind('animationDurations.chargePoint2');
}
path.animated.charge-point-3,
path.animatedReverse.charge-point-3 {
  stroke: var(--q-charge-point-stroke);
  animation-duration: v-bind('animationDurations.chargePoint3');
}
path.animated.charge-point-sum,
path.animatedReverse.charge-point-sum {
  stroke: var(--q-charge-point-stroke);
  animation-duration: v-bind('animationDurations.chargePointSum');
}

path.animated.vehicle-1,
path.animatedReverse.vehicle-1 {
  stroke: var(--q-accent);
  animation-duration: v-bind('animationDurations.vehicle1');
}
path.animated.vehicle-2,
path.animatedReverse.vehicle-2 {
  stroke: var(--q-accent);
  animation-duration: v-bind('animationDurations.vehicle2');
}
path.animated.vehicle-3,
path.animatedReverse.vehicle-3 {
  stroke: var(--q-accent);
  animation-duration: v-bind('animationDurations.vehicle3');
}

@keyframes dash {
  from {
    stroke-dashoffset: 10;
  }
  to {
    stroke-dashoffset: 0;
  }
}
@keyframes dashReverse {
  from {
    stroke-dashoffset: 0;
  }
  to {
    stroke-dashoffset: 10;
  }
}

:root {
  path.home {
    stroke: var(--q-home-stroke);
  }
}

.body--dark {
  path.home {
    stroke: var(--q-white);
  }
}

circle {
  fill: var(--q-secondary);
  fill-opacity: 1;
  stroke: var(--q-grey);
  stroke-width: v-bind(svgStrokeWidth);
  stroke-miterlimit: 2;
  stroke-opacity: 1;
}

rect {
  stroke-width: v-bind(svgStrokeWidth);
  fill: var(--q-secondary);
}

:root {
  image {
    filter: brightness(0.4); /* Creates a dark grey icons in light theme */
  }
}

.body--dark {
  image {
    filter: brightness(1); /* white icons in dark theme */
  }
}

text {
  font-size: v-bind(svgFontSize);
  line-height: 1.25;
  font-family: Arial;
  fill: var(--q-white);
  fill-opacity: 1;
}

text .fill-success {
  fill: var(--q-positive);
}

text .fill-danger {
  fill: var(--q-grid-stroke);
}

text .fill-dark {
  fill: var(--q-brown-text);
}

.grid text {
  fill: var(--q-grid-stroke);
}

.grid circle,
.grid rect {
  stroke: var(--q-grid-stroke);
}

.grid circle {
  fill: var(--q-grid-fill);
}

.pv text {
  fill: var(--q-pv-stroke);
}

.pv circle,
.pv rect {
  stroke: var(--q-pv-stroke);
}

.pv circle {
  fill: var(--q-pv-fill);
}

.battery text {
  fill: var(--q-battery-stroke);
}

.battery circle,
.battery rect {
  stroke: var(--q-battery-stroke);
}

.battery circle:not(.soc) {
  fill: var(--q-battery-fill-flow-diagram);
}


:root {
  .home text {
    fill: var(--q-brown-text); /* Brown text in light theme */
  }
}

.body--dark {
  .home text {
    fill: var(--q-white); /* White text in dark theme */
  }
}

.home circle,
.home rect {
  stroke: var(--q-home-stroke);
}

.home circle {
  fill: var(--q-home-fill);
}

.charge-point text {
  fill: var(--q-charge-point-stroke);
}

.charge-point circle,
.charge-point rect {
  stroke: var(--q-charge-point-stroke);
}

.charge-point circle {
  fill: var(--q-charge-point-fill);
}

.background-circle {
  fill: var(--q-secondary) !important;
}

.vehicle text {
  fill: var(--q-accent);
}

.vehicle circle,
.vehicle rect {
  stroke: var(--q-accent);
}

.vehicle circle:not(.soc) {
  fill: color-mix(in srgb, var(--q-accent) 50%, transparent);
}
</style>
