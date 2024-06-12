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
        (this.svgSize.xMax - this.svgSize.xMin - this.svgSize.strokeWidth) / this.svgSize.numColumns
      );
    },
    svgCircleStrokeWidth() {
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
    connectedChargers() {
      return this.mqttStore.getChargePointIds;
    },
    chargePoint1Power() {
      if (this.connectedChargers.length > 0) {
        return (
          this.mqttStore.getChargePointPower(
            this.connectedChargers[0],
            "object",
          ) || { textValue: "Loading..." }
        );
      }
      return { textValue: "N/A" };
    },
    chargePoint2Power() {
      if (this.connectedChargers.length > 1) {
        return (
          this.mqttStore.getChargePointPower(
            this.connectedChargers[1],
            "object",
          ) || { textValue: "Loading..." }
        );
      }
      return { textValue: "N/A" };
    },
    chargePoint1Name() {
      return this.mqttStore.getChargePointName(this.connectedChargers[0]);
    },
    chargePoint2Name() {
      return this.mqttStore.getChargePointName(this.connectedChargers[1]);
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
      return this.batteryPower.value > 0;
    },
    isAnimatedBatteryReverse() {
      return this.batteryPower.value < 0;
    },
    isAnimatedChargePoint1() {
      return this.chargePoint1Power.value > 0;
    },
    isAnimatedChargePoint2() {
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
    batteryClass() {
      if (this.batteryPower.value === 0) {
        return ""; // No class if battery value is zero
      } else {
        return {
          text_red: !this.BatteryPositive,
          text_green: this.BatteryPositive,
        };
      }
    },
    chargePoint1Positive() {
      return this.chargePoint1Power.value > 0;
    },
    chargePoint2Positive() {
      return this.chargePoint2Power.value > 0;
    },
  },
  methods: {
    calcRowY(row) {
      let yMin = this.svgSize.yMin + this.svgSize.strokeWidth + this.svgSize.circleRadius;
      let yMax = this.svgSize.yMax - this.svgSize.strokeWidth - this.svgSize.circleRadius;
      let yRange = yMax - yMin;
      return (
        row * (yRange / (this.svgSize.numRows - 1)) + yMin
      );
    },
    calcColumnX(column) {
      let xMin = this.svgSize.xMin + this.svgSize.strokeWidth + this.svgRectWidth / 2;
      let xMax = this.svgSize.xMax - this.svgSize.strokeWidth - this.svgRectWidth / 2;
      let xRange = xMax - xMin;
      return (
        column * (xRange / (this.svgSize.numColumns - 1)) + xMin
      );
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
    <template #headerLeft> Übersicht - Energiefluss </template>
    <i-container>
      <div class="svg-container">
        <svg
          :viewBox="svgViewBox"
          version="1.1"
          xmlns="http://www.w3.org/2000/svg"
          xmlns:svg="http://www.w3.org/2000/svg"
        >
          <defs id="defs2" />
          <g
            inkscape:label="Ebene 1"
            inkscape:groupmode="layer"
            id="layer1"
            style="display: inline"
          >
            <path
              :class="[
                { animated: isAnimatedGrid },
                { animatedReverse: isAnimatedGridReverse },
              ]"
              :d="
                'M ' +
                calcFlowLineAnchorX(0) +
                ',' +
                calcRowY(0) +
                ' ' +
                calcColumnX(1) +
                ',' +
                calcRowY(1)
              "
              class="grid"
              inkscape:connector-type="polyline"
              inkscape:connector-curvature="0"
              inkscape:connection-start="#path846"
              inkscape:connection-end="#path1109"
            />
            <path
              :class="{ animated: isAnimatedPV }"
              :d="
                'M ' +
                calcFlowLineAnchorX(2) +
                ',' +
                calcRowY(0) +
                ' ' +
                calcColumnX(1) +
                ',' +
                calcRowY(1)
              "
              class="pv"
              inkscape:connector-type="polyline"
              inkscape:connector-curvature="0"
              inkscape:connection-start="#path846-2"
              inkscape:connection-end="#path1109"
            />
            <path
              :class="{ animatedReverse: isAnimatedHome }"
              :d="
                'M ' +
                calcFlowLineAnchorX(0) +
                ',' +
                calcRowY(1) +
                ' ' +
                calcColumnX(1) +
                ',' +
                calcRowY(1)
              "
              class="home"
              inkscape:connector-type="polyline"
              inkscape:connector-curvature="0"
              inkscape:connection-start="#path846-6"
              inkscape:connection-end="#path1109"
            />
            <path
              :class="[
                { animatedReverse: isAnimatedBattery },
                { animated: isAnimatedBatteryReverse },
              ]"
              :d="
                'M ' +
                calcFlowLineAnchorX(2) +
                ',' +
                calcRowY(1) +
                ' ' +
                calcColumnX(1) +
                ',' +
                calcRowY(1)
              "
              class="battery"
              inkscape:connector-type="polyline"
              inkscape:connector-curvature="0"
              inkscape:connection-start="#path846-6-9"
              inkscape:connection-end="#path1109"
            />
            <path
              :class="{ animatedReverse: isAnimatedChargePoint1 }"
              :d="
                'M ' +
                calcFlowLineAnchorX(0) +
                ',' +
                calcRowY(2) +
                ' ' +
                calcColumnX(1) +
                ',' +
                calcRowY(1)
              "
              class="charge-point"
              inkscape:connector-type="polyline"
              inkscape:connector-curvature="0"
              inkscape:connection-start="#path846-5"
              inkscape:connection-end="#path1109"
            />
            <path
              :class="{ animatedReverse: isAnimatedChargePoint2 }"
              :d="
                'M ' +
                calcFlowLineAnchorX(2) +
                ',' +
                calcRowY(2) +
                ' ' +
                calcColumnX(1) +
                ',' +
                calcRowY(1)
              "
              class="charge-point"
              inkscape:connector-type="polyline"
              inkscape:connector-curvature="0"
              inkscape:connection-start="#path846-5-1"
              inkscape:connection-end="#path1109"
            />
          </g>

          <g
            inkscape:label="Ebene 2"
            inkscape:groupmode="layer"
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

            <!-- left side -->
            <g>
              <!-- grid -->
              <g
                class="grid"
                :transform="`translate(${calcColumnX(0)}, ${calcRowY(0)})`"
              >
                <rect
                  :x="-svgRectWidth / 2"
                  :y="-svgSize.circleRadius"
                  :width="svgRectWidth"
                  :height="svgSize.circleRadius * 2"
                  :rx="svgSize.circleRadius"
                  :ry="svgSize.circleRadius"
                />
                <g :transform="`translate(${svgSize.circleRadius - svgRectWidth / 2}, 0)`">
                  <circle cx="0" cy="0" :r="svgSize.circleRadius" />
                  <image
                    href="/icons/owbGrid.svg"
                    :x="-svgIconWidth / 2"
                    :y="-svgIconHeight / 2"
                    :height="svgIconHeight"
                    :width="svgIconWidth"
                  />
                </g>
                <text text-anchor="start">
                  <tspan
                    sodipodi:role="line"
                    :x="-svgRectWidth / 2 + 2 * svgSize.circleRadius + svgSize.strokeWidth"
                    :y="-svgSize.textSize / 2"
                  >
                    EVU
                  </tspan>
                  <tspan
                    sodipodi:role="line"
                    :class="{
                      text_green: !gridPositive,
                      text_red: gridPositive,
                    }"
                    :x="-svgRectWidth / 2 + 2 * svgSize.circleRadius + svgSize.strokeWidth"
                    :y="svgSize.textSize"
                  >
                    {{ this.gridPower.textValue }}
                  </tspan>
                </text>
              </g>

              <!-- home -->
              <g
                class="home"
                :transform="`translate(${calcColumnX(0)}, ${calcRowY(1)})`"
              >
                <rect
                  :x="-svgRectWidth / 2"
                  :y="-svgSize.circleRadius"
                  :width="svgRectWidth"
                  :height="svgSize.circleRadius * 2"
                  :rx="svgSize.circleRadius"
                  :ry="svgSize.circleRadius"
                />
                <g :transform="`translate(${svgSize.circleRadius - svgRectWidth / 2}, 0)`">
                  <circle cx="0" cy="0" :r="svgSize.circleRadius" />
                  <image
                    href="/icons/owbHouse.svg"
                    :x="-svgIconWidth / 2"
                    :y="-svgIconHeight / 2"
                    :height="svgIconHeight"
                    :width="svgIconWidth"
                  />
                </g>
                <text text-anchor="start">
                  <tspan
                    sodipodi:role="line"
                    :x="-svgRectWidth / 2 + 2 * svgSize.circleRadius + svgSize.strokeWidth"
                    :y="-svgSize.textSize / 2"
                  >
                    Haus
                  </tspan>
                  <tspan
                    sodipodi:role="line"
                    :class="{ text_green: homePositive }"
                    :x="-svgRectWidth / 2 + 2 * svgSize.circleRadius + svgSize.strokeWidth"
                    :y="svgSize.textSize"
                  >
                    {{ this.homePower.textValue }}
                  </tspan>
                </text>
              </g>

              <!-- charge point 1 -->
              <g
                class="charge-point"
                :transform="`translate(${calcColumnX(0)}, ${calcRowY(2)})`"
              >
                <rect
                  :x="-svgRectWidth / 2"
                  :y="-svgSize.circleRadius"
                  :width="svgRectWidth"
                  :height="svgSize.circleRadius * 2"
                  :rx="svgSize.circleRadius"
                  :ry="svgSize.circleRadius"
                />
                <g :transform="`translate(${svgSize.circleRadius - svgRectWidth / 2}, 0)`">
                  <circle cx="0" cy="0" :r="svgSize.circleRadius" />
                  <image
                    href="/icons/owbChargePoint.svg"
                    :x="-svgIconWidth / 2"
                    :y="-svgIconHeight / 2"
                    :height="svgIconHeight"
                    :width="svgIconWidth"
                  />
                </g>
                <text text-anchor="start">
                  <tspan
                    sodipodi:role="line"
                    :x="-svgRectWidth / 2 + 2 * svgSize.circleRadius + svgSize.strokeWidth"
                    :y="-svgSize.textSize / 2"
                  >
                    {{ chargePoint1Name }}
                  </tspan>
                  <tspan
                    sodipodi:role="line"
                    :class="{ text_green: chargePoint1Positive }"
                    :x="-svgRectWidth / 2 + 2 * svgSize.circleRadius + svgSize.strokeWidth"
                    :y="svgSize.textSize"
                  >
                    {{ this.chargePoint1Power.textValue }}
                  </tspan>
                </text>
              </g>

              <!-- vehicle at charge point 1 -->
              <g
                class="vehicle"
                :transform="`translate(${calcColumnX(0)}, ${calcRowY(3)})`"
              >
                <rect
                  :x="-svgRectWidth / 2"
                  :y="-svgSize.circleRadius"
                  :width="svgRectWidth"
                  :height="svgSize.circleRadius * 2"
                  :rx="svgSize.circleRadius"
                  :ry="svgSize.circleRadius"
                />
                <g :transform="`translate(${svgSize.circleRadius - svgRectWidth / 2}, 0)`">
                  <circle cx="0" cy="0" :r="svgSize.circleRadius" />
                  <image
                    href="/icons/owbVehicle.svg"
                    :x="-svgIconWidth / 2"
                    :y="-svgIconHeight / 2"
                    :height="svgIconHeight"
                    :width="svgIconWidth"
                  />
                </g>
                <text text-anchor="start">
                  <tspan
                    sodipodi:role="line"
                    :x="-svgRectWidth / 2 + 2 * svgSize.circleRadius + svgSize.strokeWidth"
                    :y="-svgSize.textSize / 2"
                  >
                    Vehicle 1
                  </tspan>
                  <tspan
                    sodipodi:role="line"
                    :class="{ text_green: chargePoint1Positive }"
                    :x="-svgRectWidth / 2 + 2 * svgSize.circleRadius + svgSize.strokeWidth"
                    :y="svgSize.textSize"
                  >
                    Charge Mode
                  </tspan>
                </text>
              </g>
            </g>

            <!-- right side -->
            <g>
              <!-- pv -->
              <g
                class="pv"
                :transform="`translate(${calcColumnX(2)}, ${calcRowY(0)})`"
              >
                <rect
                  :x="-svgRectWidth / 2"
                  :y="-svgSize.circleRadius"
                  :width="svgRectWidth"
                  :height="svgSize.circleRadius * 2"
                  :rx="svgSize.circleRadius"
                  :ry="svgSize.circleRadius"
                />
                <g :transform="`translate(${svgSize.circleRadius - svgRectWidth / 2}, 0)`">
                  <circle cx="0" cy="0" :r="svgSize.circleRadius" />
                  <image
                    href="/icons/owbPV.svg"
                    :x="-svgIconWidth / 2"
                    :y="-svgIconHeight / 2"
                    :height="svgIconHeight"
                    :width="svgIconWidth"
                  />
                </g>
                <text text-anchor="start">
                  <tspan
                    sodipodi:role="line"
                    :x="-svgRectWidth / 2 + 2 * svgSize.circleRadius + svgSize.strokeWidth"
                    :y="-svgSize.textSize / 2"
                  >
                    PV
                  </tspan>
                  <tspan
                    sodipodi:role="line"
                    :class="{ text_green: pvPositive }"
                    :x="-svgRectWidth / 2 + 2 * svgSize.circleRadius + svgSize.strokeWidth"
                    :y="svgSize.textSize"
                  >
                    {{ this.pvPower.textValue }}
                  </tspan>
                </text>
              </g>

              <!-- battery -->
              <g
                class="battery"
                :transform="`translate(${calcColumnX(2)}, ${calcRowY(1)})`"
              >
                <rect
                  :x="-svgRectWidth / 2"
                  :y="-svgSize.circleRadius"
                  :width="svgRectWidth"
                  :height="svgSize.circleRadius * 2"
                  :rx="svgSize.circleRadius"
                  :ry="svgSize.circleRadius"
                />
                <g :transform="`translate(${svgSize.circleRadius - svgRectWidth / 2}, 0)`">
                  <circle cx="0" cy="0" :r="svgSize.circleRadius" />
                  <image
                    href="/icons/owbBattery.svg"
                    :x="-svgIconWidth / 2"
                    :y="-svgIconHeight / 2"
                    :height="svgIconHeight"
                    :width="svgIconWidth"
                  />
                </g>
                <text text-anchor="start">
                  <tspan
                    sodipodi:role="line"
                    :x="-svgRectWidth / 2 + 2 * svgSize.circleRadius + svgSize.strokeWidth"
                    :y="-svgSize.textSize / 2"
                  >
                    Speicher
                  </tspan>
                  <tspan
                    sodipodi:role="line"
                    :class="{ text_green: batteryPositive }"
                    :x="-svgRectWidth / 2 + 2 * svgSize.circleRadius + svgSize.strokeWidth"
                    :y="svgSize.textSize"
                  >
                    {{ this.batteryPower.textValue }}
                  </tspan>
                </text>
              </g>

              <!-- charge point 2 -->
              <g
                class="charge-point"
                :transform="`translate(${calcColumnX(2)}, ${calcRowY(2)})`"
              >
                <rect
                  :x="-svgRectWidth / 2"
                  :y="-svgSize.circleRadius"
                  :width="svgRectWidth"
                  :height="svgSize.circleRadius * 2"
                  :rx="svgSize.circleRadius"
                  :ry="svgSize.circleRadius"
                />
                <g :transform="`translate(${svgSize.circleRadius - svgRectWidth / 2}, 0)`">
                  <circle cx="0" cy="0" :r="svgSize.circleRadius" />
                  <image
                    href="/icons/owbChargePoint.svg"
                    :x="-svgIconWidth / 2"
                    :y="-svgIconHeight / 2"
                    :height="svgIconHeight"
                    :width="svgIconWidth"
                  />
                </g>
                <text text-anchor="start">
                  <tspan
                    sodipodi:role="line"
                    :x="-svgRectWidth / 2 + 2 * svgSize.circleRadius + svgSize.strokeWidth"
                    :y="-svgSize.textSize / 2"
                  >
                    {{ chargePoint2Name }}
                  </tspan>
                  <tspan
                    sodipodi:role="line"
                    :class="{ text_green: chargePoint2Positive }"
                    :x="-svgRectWidth / 2 + 2 * svgSize.circleRadius + svgSize.strokeWidth"
                    :y="svgSize.textSize"
                  >
                    {{ this.chargePoint2Power.textValue }}
                  </tspan>
                </text>
              </g>

              <!-- vehicle at charge point 2 -->
              <g
                class="vehicle"
                :transform="`translate(${calcColumnX(2)}, ${calcRowY(3)})`"
              >
                <rect
                  :x="-svgRectWidth / 2"
                  :y="-svgSize.circleRadius"
                  :width="svgRectWidth"
                  :height="svgSize.circleRadius * 2"
                  :rx="svgSize.circleRadius"
                  :ry="svgSize.circleRadius"
                />
                <g :transform="`translate(${svgSize.circleRadius - svgRectWidth / 2}, 0)`">
                  <circle cx="0" cy="0" :r="svgSize.circleRadius" />
                  <image
                    href="/icons/owbVehicle.svg"
                    :x="-svgIconWidth / 2"
                    :y="-svgIconHeight / 2"
                    :height="svgIconHeight"
                    :width="svgIconWidth"
                  />
                </g>
                <text text-anchor="start">
                  <tspan
                    sodipodi:role="line"
                    :x="-svgRectWidth / 2 + 2 * svgSize.circleRadius + svgSize.strokeWidth"
                    :y="-svgSize.textSize / 2"
                  >
                    Vehicle 2
                  </tspan>
                  <tspan
                    sodipodi:role="line"
                    :class="{ text_green: chargePoint2Positive }"
                    :x="-svgRectWidth / 2 + 2 * svgSize.circleRadius + svgSize.strokeWidth"
                    :y="svgSize.textSize"
                  >
                    Charge Mode
                  </tspan>
                </text>
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

circle {
  fill: black;
  fill-opacity: 1;
  stroke: gray;
  stroke-width: v-bind(svgCircleStrokeWidth);
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

text .text_green {
  fill: var(--color--success);
  /* or any color you prefer for positive values */
}

text .text_red {
  fill: var(--color--danger);
  /* or any color you prefer for negative values */
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

.battery circle {
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

.vehicle circle {
  fill: var(--color--teal-85);
}
</style>
