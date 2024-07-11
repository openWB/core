<script>
import { useMqttStore } from "@/stores/mqtt.js";
import DashBoardCard from "@/components/DashBoardCard.vue";

export default {
  name: "DashboardFlowCard",
  components: {
    DashBoardCard,
  },
  props: {
    changesLocked: { required: false, type: Boolean, default: false },
  },
  data() {
    return {
      mqttStore: useMqttStore(),
      svgSize: {
        xMin: 0, // viewBox min x
        xMax: 150, // viewBox max x
        yMin: 0, // viewBox min y
        yMax: 105, // viewBox max y
        circleRadius: 10,
        strokeWidth: 0.5,
        textSize: 5,
        numRows: 4,
        numColumns: 3,
      },
    };
  },
  computed: {
    // calculated svg coordinates
    svgViewBox() {
      return `${this.svgSize.xMin} ${this.svgSize.yMin} ${this.svgSize.xMax} ${this.svgSize.yMax}`;
    },
    svgFontSize() {
      return `${this.svgSize.textSize}px`;
    },
    svgRectWidth() {
      return (
        (this.svgSize.xMax - this.svgSize.xMin - this.svgSize.strokeWidth) /
        this.svgSize.numColumns
      );
    },
    svgStrokeWidth() {
      return this.svgSize.strokeWidth;
    },
    svgIconWidth() {
      return this.svgSize.circleRadius;
    },
    svgIconHeight() {
      return this.svgSize.circleRadius;
    },

    // component values
    gridPower() {
      return this.mqttStore.getGridPower("object");
    },
    pvPower() {
      return this.mqttStore.getPvPower("object");
    },
    homePower() {
      return this.mqttStore.getHomePower("object");
    },
    batteryPower() {
      return this.mqttStore.getBatteryPower("object");
    },
    batterySoc() {
      return this.mqttStore.getBatterySoc("object").value / 100;
    },
    connectedChargePoints() {
      return this.mqttStore.getChargePointIds;
    },
    chargePoint1Power() {
      if (this.connectedChargePoints.length > 0) {
        return (
          this.mqttStore.getChargePointPower(
            this.connectedChargePoints[0],
            "object",
          ) || { textValue: "Loading..." }
        );
      }
      return { textValue: "N/A" };
    },
    chargePoint2Power() {
      if (this.connectedChargePoints.length > 1) {
        return (
          this.mqttStore.getChargePointPower(
            this.connectedChargePoints[1],
            "object",
          ) || { textValue: "Loading..." }
        );
      }
      return { textValue: "N/A" };
    },
    chargePoint1Name() {
      return this.mqttStore.getChargePointName(this.connectedChargePoints[0]);
    },
    chargePoint2Name() {
      return this.mqttStore.getChargePointName(this.connectedChargePoints[1]);
    },
    chargePoint1VehicleConnected() {
      return this.mqttStore.getChargePointPlugState(
        this.connectedChargePoints[0],
      );
    },
    chargePoint2VehicleConnected() {
      return this.mqttStore.getChargePointPlugState(
        this.connectedChargePoints[1],
      );
    },
    chargePoint1ConnectedVehicleName() {
      return this.mqttStore.getChargePointConnectedVehicleName(
        this.connectedChargePoints[0],
      );
    },
    chargePoint2ConnectedVehicleName() {
      return this.mqttStore.getChargePointConnectedVehicleName(
        this.connectedChargePoints[1],
      );
    },
    chargePoint1ConnectedVehicleChargeMode() {
      return this.mqttStore.getChargePointConnectedVehicleChargeMode(
        this.connectedChargePoints[0],
      );
    },
    chargePoint2ConnectedVehicleChargeMode() {
      return this.mqttStore.getChargePointConnectedVehicleChargeMode(
        this.connectedChargePoints[1],
      );
    },
    chargePoint1ConnectedVehicleSoc() {
      return (
        this.mqttStore.getChargePointConnectedVehicleSoc(
          this.connectedChargePoints[0],
        ).soc / 100
      );
    },
    chargePoint2ConnectedVehicleSoc() {
      return (
        this.mqttStore.getChargePointConnectedVehicleSoc(
          this.connectedChargePoints[1],
        ).soc / 100
      );
    },
    isAnimatedGrid() {
      return this.gridPower.value > 0;
    },
    isAnimatedGridReverse() {
      return this.gridPower.value < 0;
    },
    isAnimatedPV() {
      return this.pvPower.value > 100;
    },
    isAnimatedHome() {
      return this.homePower.value > 0;
    },
    isAnimatedBattery() {
      return this.batteryPower.value < 0;
    },
    isAnimatedBatteryReverse() {
      return this.batteryPower.value > 0;
    },
    isAnimatedChargePoint1() {
      return this.chargePoint1Power.value < 0;
    },
    isAnimatedChargePoint1Reverse() {
      return this.chargePoint1Power.value > 0;
    },
    isAnimatedChargePoint2() {
      return this.chargePoint2Power.value < 0;
    },
    isAnimatedChargePoint2Reverse() {
      return this.chargePoint2Power.value > 0;
    },
    gridPositive() {
      return this.gridPower.value > 0;
    },
    pvPositive() {
      return this.pvPower.value > 100;
    },
    homePositive() {
      return this.homePower.value > 0;
    },
    batteryPositive() {
      return this.batteryPower.value > 0;
    },
    chargePoint1Positive() {
      return this.chargePoint1Power.value > 0;
    },
    chargePoint2Positive() {
      return this.chargePoint2Power.value > 0;
    },
    svgComponents() {
      var components = [];
      if (this.mqttStore.getThemeConfiguration.enable_dashboard_card_grid) {
        components.push({
          id: "grid",
          class: {
            base: "grid",
            valueLabel: this.gridPositive ? "fill-danger" : "fill-success",
            animated: this.isAnimatedGrid,
            animatedReverse: !this.gridPositive,
          },
          position: {
            row: 0,
            column: 0,
          },
          label: ["EVU", this.gridPower.textValue],
          icon: "icons/owbGrid.svg",
        });
      }
      if (
        this.mqttStore.getThemeConfiguration
          .enable_dashboard_card_home_consumption
      ) {
        components.push({
          id: "home",
          class: {
            base: "home",
            valueLabel: "",
            animated: this.isAnimatedHome,
            animatedReverse: this.homePositive,
          },
          position: {
            row: 0,
            column: 2,
          },
          label: ["Haus", this.homePower.textValue],
          icon: "icons/owbHouse.svg",
        });
      }
      if (
        this.mqttStore.getPvConfigured &&
        this.mqttStore.getThemeConfiguration.enable_dashboard_card_inverter_sum
      ) {
        components.push({
          id: "pv",
          class: {
            base: "pv",
            valueLabel: this.pvPositive ? "fill-success" : "",
            animated: this.isAnimatedPV,
            animatedReverse: !this.pvPositive,
          },
          position: {
            row: 1,
            column: 0,
          },
          label: ["PV", this.pvPower.textValue],
          icon: "icons/owbPV.svg",
        });
      }
      if (
        this.mqttStore.getBatteryConfigured &&
        this.mqttStore.getThemeConfiguration.enable_dashboard_card_battery_sum
      ) {
        components.push({
          id: "battery",
          class: {
            base: "battery",
            valueLabel: "",
            animated: this.isAnimatedBattery,
            animatedReverse: this.isAnimatedBatteryReverse,
          },
          position: {
            row: 1,
            column: 2,
          },
          label: ["Speicher", this.batteryPower.textValue],
          soc: this.batterySoc,
          icon: "icons/owbBattery.svg",
        });
      }
      if (
        this.connectedChargePoints.length > 0 &&
        this.mqttStore.getThemeConfiguration
          .enable_dashboard_card_charge_point_sum
      ) {
        components.push({
          id: "charge-point-1",
          class: {
            base: "charge-point",
            valueLabel: "",
            animated: this.isAnimatedChargePoint1,
            animatedReverse: this.isAnimatedChargePoint1Reverse,
          },
          position: {
            row: 2,
            column: 0,
          },
          label: [this.chargePoint1Name, this.chargePoint1Power.textValue],
          icon: "icons/owbChargePoint.svg",
        });
      }
      if (
        this.connectedChargePoints.length > 1 &&
        this.mqttStore.getThemeConfiguration
          .enable_dashboard_card_charge_point_sum
      ) {
        components.push({
          id: "charge-point-2",
          class: {
            base: "charge-point",
            valueLabel: "",
            animated: this.isAnimatedChargePoint2,
            animatedReverse: this.isAnimatedChargePoint2Reverse,
          },
          position: {
            row: 2,
            column: 2,
          },
          label: [this.chargePoint2Name, this.chargePoint2Power.textValue],
          icon: "icons/owbChargePoint.svg",
        });
      }
      if (
        this.chargePoint1VehicleConnected &&
        this.mqttStore.getThemeConfiguration.enable_dashboard_card_vehicles
      ) {
        components.push({
          id: "vehicle-1",
          class: {
            base: "vehicle",
            valueLabel:
              "fill-" + this.chargePoint2ConnectedVehicleChargeMode.class,
          },
          position: {
            row: 3,
            column: 0,
          },
          label: [
            this.chargePoint1ConnectedVehicleName || "---",
            this.chargePoint1ConnectedVehicleChargeMode.label || "---",
          ],
          soc: this.chargePoint1ConnectedVehicleSoc,
          icon: "icons/owbVehicle.svg",
        });
      }
      if (
        this.chargePoint2VehicleConnected &&
        this.mqttStore.getThemeConfiguration.enable_dashboard_card_vehicles
      ) {
        components.push({
          id: "vehicle-2",
          class: {
            base: "vehicle",
            valueLabel:
              "fill-" + this.chargePoint2ConnectedVehicleChargeMode.class,
          },
          position: {
            row: 3,
            column: 2,
          },
          label: [
            this.chargePoint2ConnectedVehicleName || "---",
            this.chargePoint2ConnectedVehicleChargeMode.label || "---",
          ],
          soc: this.chargePoint2ConnectedVehicleSoc,
          icon: "icons/owbVehicle.svg",
        });
      }
      return components;
    },
  },
  methods: {
    calcRowY(row) {
      let yMin =
        this.svgSize.yMin +
        this.svgSize.strokeWidth +
        this.svgSize.circleRadius;
      let yMax =
        this.svgSize.yMax -
        this.svgSize.strokeWidth -
        this.svgSize.circleRadius;
      let yRange = yMax - yMin;
      return row * (yRange / (this.svgSize.numRows - 1)) + yMin;
    },
    calcColumnX(column) {
      let xMin =
        this.svgSize.xMin + this.svgSize.strokeWidth + this.svgRectWidth / 2;
      let xMax =
        this.svgSize.xMax - this.svgSize.strokeWidth - this.svgRectWidth / 2;
      let xRange = xMax - xMin;
      return column * (xRange / (this.svgSize.numColumns - 1)) + xMin;
    },
    calcFlowLineAnchorX(column) {
      let columnX = this.calcColumnX(column);
      if (column < this.svgSize.numColumns / 2)
        return columnX + this.svgRectWidth / 2 - this.svgSize.circleRadius;
      else if (column > this.svgSize.numColumns / 2)
        return columnX - this.svgRectWidth / 2 + this.svgSize.circleRadius;
      return columnX;
    },
  },
};
</script>

<template>
  <dash-board-card color="primary">
    <template #headerLeft>
      Übersicht - Energiefluss
    </template>
    <i-container>
      <div class="svg-container">
        <svg
          :viewBox="svgViewBox"
          version="1.1"
          xmlns="http://www.w3.org/2000/svg"
          xmlns:svg="http://www.w3.org/2000/svg"
        >
          <g
            id="layer1"
            style="display: inline"
          >
            <path
              v-for="component in svgComponents"
              :key="component.id"
              :class="[
                component.class.base,
                { animated: component.class.animated },
                { animatedReverse: component.class.animatedReverse },
              ]"
              :d="
                component.class.base !== 'vehicle'
                  ? `M ${calcFlowLineAnchorX(component.position.column)}, ` +
                    `${calcRowY(component.position.row)} ${calcColumnX(1)}, ${calcRowY(1)}`
                  : ''
              "
            />
          </g>

          <g
            id="layer2"
            style="display: inline"
          >
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
            >
              <rect
                :x="-svgRectWidth / 2"
                :y="-svgSize.circleRadius"
                :width="svgRectWidth"
                :height="svgSize.circleRadius * 2"
                :rx="svgSize.circleRadius"
                :ry="svgSize.circleRadius"
              />
              <g
                :transform="`translate(${svgSize.circleRadius - svgRectWidth / 2}, 0)`"
              >
                <defs>
                  <clipPath
                    v-if="component.soc"
                    :id="`clip-soc-${component.id}`"
                  >
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
                </defs>
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
              <text text-anchor="start">
                <tspan
                  :x="
                    -svgRectWidth / 2 +
                      2 * svgSize.circleRadius +
                      svgSize.strokeWidth
                  "
                  :y="-svgSize.textSize / 2"
                >
                  {{ component.label[0] }}
                </tspan>
                <tspan
                  :class="component.class.valueLabel"
                  :x="
                    -svgRectWidth / 2 +
                      2 * svgSize.circleRadius +
                      svgSize.strokeWidth
                  "
                  :y="svgSize.textSize"
                >
                  {{ component.label[1] }}
                </tspan>
              </text>
            </g>
          </g>
        </svg>
      </div>
    </i-container>
  </dash-board-card>
</template>

<style scoped>
.svg-container {
  display: flex;
  flex-direction: column;
  align-items: center;
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

path.animated {
  stroke: white;
  stroke-dasharray: 5;
  animation: dash 1s linear infinite;
}

path.animatedReverse {
  stroke: white;
  stroke-dasharray: 5;
  animation: dashReverse 1s linear infinite;
}

path.animated.grid {
  stroke: var(--color--danger);
}

path.animatedReverse.grid {
  stroke: var(--color--success);
}

path.animated.pv,
path.animatedReverse.pv {
  stroke: var(--color--success);
}

path.animated.battery,
path.animatedReverse.battery {
  stroke: var(--color--warning);
}

path.animated.charge-point,
path.animatedReverse.charge-point {
  stroke: var(--color--primary);
}

circle {
  fill: black;
  fill-opacity: 1;
  stroke: gray;
  stroke-width: v-bind(svgStrokeWidth);
  stroke-miterlimit: 2;
  stroke-opacity: 1;
}

rect {
  stroke-width: v-bind(svgStrokeWidth);
}

@keyframes dash {
  to {
    stroke-dashoffset: -20;
  }
}

@keyframes dashReverse {
  to {
    stroke-dashoffset: 20;
  }
}

text {
  font-size: v-bind(svgFontSize);
  line-height: 1.25;
  font-family: Arial;
  fill: white;
  fill-opacity: 1;
}

text .fill-success {
  fill: var(--color--success);
}

text .fill-danger {
  fill: var(--color--danger);
}

text .fill-dark {
  fill: var(--color--dark);
}

.grid text {
  fill: var(--color--danger);
}

.grid circle,
.grid rect {
  stroke: var(--color--danger);
}

.grid circle {
  fill: var(--color--danger-90);
}

.pv text {
  fill: var(--color--success);
}

.pv circle,
.pv rect {
  stroke: var(--color--success);
}

.pv circle {
  fill: var(--color--success-90);
}

.battery text {
  fill: var(--color--warning);
}

.battery circle,
.battery rect {
  stroke: var(--color--warning);
}

.battery circle:not(.soc) {
  fill: var(--color--warning-90);
}

.home text {
  fill: var(--color--light);
}

.home circle,
.home rect {
  stroke: var(--color--light);
}

.home circle {
  fill: var(--color--dark-70);
}

.charge-point text {
  fill: var(--color--primary);
}

.charge-point circle,
.charge-point rect {
  stroke: var(--color--primary);
}

.charge-point circle {
  fill: var(--color--primary-85);
}

.vehicle text {
  fill: var(--color--teal);
}

.vehicle circle,
.vehicle rect {
  stroke: var(--color--teal);
}

.vehicle circle:not(.soc) {
  fill: var(--color--teal-85);
}
</style>
