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
        (this.svgSize.xMax - this.svgSize.xMin - this.svgSize.strokeWidth - this.svgSize.numColumns) /
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
    chargePointSumPower() {
      return this.mqttStore.getChargePointSumPower("object");
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
    chargePoint3Power() {
      if (this.connectedChargePoints.length > 2) {
        return (
          this.mqttStore.getChargePointPower(
            this.connectedChargePoints[2],
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
    chargePoint3Name() {
      return this.mqttStore.getChargePointName(this.connectedChargePoints[2]);
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
    chargePoint3VehicleConnected() {
      return this.mqttStore.getChargePointPlugState(
        this.connectedChargePoints[2],
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
    chargePoint3ConnectedVehicleName() {
      return this.mqttStore.getChargePointConnectedVehicleName(
        this.connectedChargePoints[2],
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
    chargePoint3ConnectedVehicleChargeMode() {
      return this.mqttStore.getChargePointConnectedVehicleChargeMode(
        this.connectedChargePoints[2],
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
    chargePoint3ConnectedVehicleSoc() {
      return (
        this.mqttStore.getChargePointConnectedVehicleSoc(
          this.connectedChargePoints[2],
        ).soc / 100
      );
    },
    gridConsumption() {
      return this.gridPower.value > 0;
    },
    gridFeedIn() {
      return this.gridPower.value < 0;
    },
    homeConsumption() {
      return this.homePower.value > 0;
    },
    homeProduction() {
      return this.homePower.value < 0;
    },
    pvProduction() {
      return this.pvPower.value > 0;
    },
    batteryDischarging() {
      return this.batteryPower.value < 0;
    },
    batteryCharging() {
      return this.batteryPower.value > 0;
    },
    chargePointSumCharging() {
      return this.chargePointSumPower.value > 0;
    },
    chargePointSumDischarging() {
      return this.chargePointSumPower.value < 0;
    },
    chargePoint1Charging() {
      return this.chargePoint1Power.value > 0;
    },
    chargePoint1Discharging() {
      return this.chargePoint1Power.value < 0;
    },
    chargePoint2Charging() {
      return this.chargePoint2Power.value > 0;
    },
    chargePoint2Discharging() {
      return this.chargePoint2Power.value < 0;
    },
    chargePoint3Charging() {
      return this.chargePoint3Power.value > 0;
    },
    chargePoint3Discharging() {
      return this.chargePoint3Power.value < 0;
    },
    svgComponents() {
      var components = [];
      // add grid component
      if (this.mqttStore.getThemeConfiguration.enable_dashboard_card_grid) {
        components.push({
          id: "grid",
          class: {
            base: "grid",
            valueLabel: this.gridFeedIn ? "fill-success" : (this.gridConsumption ? "fill-danger" : ""),
            animated: this.gridConsumption,
            animatedReverse: this.gridFeedIn,
          },
          position: {
            row: 0,
            column: 0,
          },
          label: ["EVU", this.gridPower.textValue],
          icon: "icons/owbGrid.svg",
        });
      }
      // add home component
      if (
        this.mqttStore.getThemeConfiguration
          .enable_dashboard_card_home_consumption
      ) {
        components.push({
          id: "home",
          class: {
            base: "home",
            valueLabel: "",
            animated: this.homeProduction,
            animatedReverse: this.homeConsumption,
          },
          position: {
            row: 0,
            column: 2,
          },
          label: ["Haus", this.homePower.textValue],
          icon: "icons/owbHouse.svg",
        });
      }
      // add pv sum component
      if (
        this.mqttStore.getPvConfigured &&
        this.mqttStore.getThemeConfiguration.enable_dashboard_card_inverter_sum
      ) {
        components.push({
          id: "pv",
          class: {
            base: "pv",
            valueLabel: this.pvProduction ? "fill-success" : "",
            animated: this.pvProduction,
            animatedReverse: false,
          },
          position: {
            row: 1,
            column: 0,
          },
          label: ["PV", this.pvPower.textValue],
          icon: "icons/owbPV.svg",
        });
      }
      // add battery sum component
      if (
        this.mqttStore.getBatteryConfigured &&
        this.mqttStore.getThemeConfiguration.enable_dashboard_card_battery_sum
      ) {
        components.push({
          id: "battery",
          class: {
            base: "battery",
            valueLabel: "",
            animated: this.batteryDischarging,
            animatedReverse: this.batteryCharging,
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
      // charge point and vehicle components
      if (
        this.connectedChargePoints.length > 0 &&
        this.mqttStore.getThemeConfiguration
          .enable_dashboard_card_charge_point_sum
      ) {
        if (this.connectedChargePoints.length <= 3) {
          // add charge point 1 component
          components.push({
            id: "charge-point-1",
            class: {
              base: "charge-point",
              valueLabel: "",
              animated: this.chargePoint1Discharging,
              animatedReverse: this.chargePoint1Charging,
            },
            position: {
              row: 2,
              column: this.connectedChargePoints.length > 1 ? 0 : 1,
            },
            label: [this.chargePoint1Name, this.chargePoint1Power.textValue],
            icon: "icons/owbChargePoint.svg",
          });
          if (
            this.chargePoint1VehicleConnected &&
            this.mqttStore.getThemeConfiguration.enable_dashboard_card_vehicles
          ) {
            // add vehicle 1 component
            components.push({
              id: "vehicle-1",
              class: {
                base: "vehicle",
                valueLabel:
                  "fill-" + this.chargePoint1ConnectedVehicleChargeMode.class,
              },
              position: {
                row: 3,
                column: this.connectedChargePoints.length > 1 ? 0 : 1,
              },
              label: [
                this.chargePoint1ConnectedVehicleName || "---",
                this.chargePoint1ConnectedVehicleChargeMode.label || "---",
              ],
              soc: this.chargePoint1ConnectedVehicleSoc,
              icon: "icons/owbVehicle.svg",
            });
          }
          if (this.connectedChargePoints.length > 1) {
            // add charge point 2 component
            components.push({
              id: "charge-point-2",
              class: {
                base: "charge-point",
                valueLabel: "",
                animated: this.chargePoint2Discharging,
                animatedReverse: this.chargePoint2Charging,
              },
              position: {
                row: 2,
                column: this.connectedChargePoints.length > 2 ? 1 : 2,
              },
              label: [this.chargePoint2Name, this.chargePoint2Power.textValue],
              icon: "icons/owbChargePoint.svg",
            });
            if (
              this.chargePoint2VehicleConnected &&
              this.mqttStore.getThemeConfiguration.enable_dashboard_card_vehicles
            ) {
              // add vehicle 2 component
              components.push({
                id: "vehicle-2",
                class: {
                  base: "vehicle",
                  valueLabel:
                    "fill-" + this.chargePoint2ConnectedVehicleChargeMode.class,
                },
                position: {
                  row: 3,
                  column: this.connectedChargePoints.length > 2 ? 1 : 2,
                },
                label: [
                  this.chargePoint2ConnectedVehicleName || "---",
                  this.chargePoint2ConnectedVehicleChargeMode.label || "---",
                ],
                soc: this.chargePoint2ConnectedVehicleSoc,
                icon: "icons/owbVehicle.svg",
              });
            }
            if (this.connectedChargePoints.length > 2) {
              // add charge point 3 component
              components.push({
                id: "charge-point-3",
                class: {
                  base: "charge-point",
                  valueLabel: "",
                  animated: this.chargePoint3Discharging,
                  animatedReverse: this.chargePoint3Charging,
                },
                position: {
                  row: 2,
                  column: 2,
                },
                label: [this.chargePoint3Name, this.chargePoint3Power.textValue],
                icon: "icons/owbChargePoint.svg",
              });
              if (
                this.chargePoint3VehicleConnected &&
                this.mqttStore.getThemeConfiguration.enable_dashboard_card_vehicles
              ) {
                // add vehicle 3 component
                components.push({
                  id: "vehicle-3",
                  class: {
                    base: "vehicle",
                    valueLabel:
                      "fill-" + this.chargePoint3ConnectedVehicleChargeMode.class,
                  },
                  position: {
                    row: 3,
                    column: 2,
                  },
                  label: [
                    this.chargePoint3ConnectedVehicleName || "---",
                    this.chargePoint3ConnectedVehicleChargeMode.label || "---",
                  ],
                  soc: this.chargePoint3ConnectedVehicleSoc,
                  icon: "icons/owbVehicle.svg",
                });
              }
            }
          }
        } else {
          // add charge point sum component
          components.push({
            id: "charge-point-sum",
            class: {
              base: "charge-point",
              valueLabel: "",
              animated: this.chargePointSumDischarging,
              animatedReverse: this.chargePointSumCharging,
            },
            position: {
              row: 2,
              column: 1,
            },
            label: ["Ladepunkte", this.chargePointSumPower.textValue],
            icon: "icons/owbChargePoint.svg",
          })
        }
      }
      // set number of rows if no vehicles displayed
      if (
        !this.mqttStore.getThemeConfiguration.enable_dashboard_card_vehicles ||
        this.connectedChargePoints.length === 0 ||
        this.connectedChargePoints.length > 3
      ) {
        this.setSvgNumRows(3);
      }
      return components;
    },
  },
  methods: {
    setSvgNumRows(numRows) {
      this.svgSize.numRows = numRows;
    },
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
      if (column < (this.svgSize.numColumns - 1) / 2) {
        return columnX + this.svgRectWidth / 2 - this.svgSize.circleRadius;
      }
      else if (column > (this.svgSize.numColumns - 1) / 2) {
        return columnX - this.svgRectWidth / 2 + this.svgSize.circleRadius;
      }
      return columnX;
    },
    calcSvgElementBoundingBox(elementId) {
      let element = document.getElementById(elementId);
      if (element == undefined){
        return { x: 0, y: 0, width: 0, height: 0 };
      }
      let boundingBox = element.getBBox();
      return {
        x: boundingBox.x,
        y: boundingBox.y,
        width: boundingBox.width,
        height: boundingBox.height,
      };
    },
    beginAnimation(elementId) {
      if (this.$refs[elementId] == undefined){
        return;
      }
      this.$refs[elementId][0]?.beginElement();
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
              @click="beginAnimation(`animate-label-${component.id}`)"
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
              <text
                :clip-path="`url(#clip-label-${component.id})`"
              >
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
                    v-if="calcSvgElementBoundingBox(`label-${component.id}`).width > svgRectWidth - 2 * svgSize.circleRadius - 2 * svgSize.strokeWidth"
                    :ref="`animate-label-${component.id}`"
                    xmlns="http://www.w3.org/2000/svg"
                    attributeName="x"
                    dur="5s"
                    :values="
                      '0; ' +
                        (- calcSvgElementBoundingBox(`label-${component.id}`).width
                          + svgRectWidth - 2.5 * svgSize.circleRadius - 2 * svgSize.strokeWidth) + '; 0;'
                    "
                    repeatCount="0"
                    begin="2s"
                    additive="sum"
                  />
                  {{ component.label[0] }}
                </tspan>
                <tspan
                  :id="`value-${component.id}`"
                  :class="component.class.valueLabel"
                  text-anchor="end"
                  :x="
                    2 * svgSize.circleRadius +
                      svgSize.strokeWidth
                  "
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
