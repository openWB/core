<script>
import { useMqttStore } from "@/stores/mqtt.js";
import DashBoardCard from "@/components/DashBoardCard.vue";

export default {
  name: "DashboardCanvasView",
  components: {
    DashBoardCard,
  },
  props: {
    changesLocked: { required: false, type: Boolean, default: false },
  },
  data() {
    return {
      mqttStore: useMqttStore()
    };
  },
  computed: {
    gridPower() {
      return this.mqttStore.getGridPower('object');
    },
    pvPower() {
      return this.mqttStore.getPvPower('object');
    },
    homePower() {
      return this.mqttStore.getHomePower('object');
    },
    batteryPower() {
      return this.mqttStore.getBatteryPower('object');
    },
    connectedChargers() {
      return this.mqttStore.getChargePointIds;
    },
    chargePoint1Power() {
      if (this.connectedChargers.length > 0) {
        return this.mqttStore.getChargePointPower(this.connectedChargers[0], 'object') || { textValue: "Loading..." };
      }
      return { textValue: "N/A" };
    },
    chargePoint2Power() {
      if (this.connectedChargers.length > 1) {
        return this.mqttStore.getChargePointPower(this.connectedChargers[1], 'object') || { textValue: "Loading..." };
      }
      return { textValue: "N/A" };
    },
    isAnimatedEVU() {
      return this.gridPower.value > 0;
    },
    isAnimatedEVUReverse() {
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
    isAnimatedCharge1() {
      return this.chargePoint1Power.value > 0;
    },
    isAnimatedCharge2() {
      return this.chargePoint2Power.value > 0;
    },
    EVUPositive() {
      return this.gridPower.value > 0;
    },
    PVPositive() {
      return this.pvPower.value > 100;
    },
    HomePositive() {
      return this.homePower.value > 0;
    },
    BatteryPositive() {
      return this.batteryPower.value > 0;
    },
    batteryClass() {
      if (this.batteryPower.value === 0) {
        return ''; // No class if battery value is zero
      } else {
        return {
          text_red: !this.BatteryPositive,
          text_green: this.BatteryPositive
        };
      }
    },
    LP1Positive() {
      return this.chargePoint1Power.value > 0;
    },
    LP2Positive() {
      return this.chargePoint2Power.value > 0;
    }
  },
};
</script>

<template>
  <dash-board-card color="primary">
    <template #headerLeft> Übersicht - Energiefluss </template>
    <i-container>
      <div class="svg-container">
        <svg viewBox="0 0 170.09999 121.70834" version="1.1" id="diagram"
          xmlns="http://www.w3.org/2000/svg" xmlns:svg="http://www.w3.org/2000/svg">
          <defs id="defs2" />
          <g inkscape:label="Ebene 1" inkscape:groupmode="layer" id="layer1" style="display:inline">
            <path :class="[{ animated: isAnimatedEVU }, { animatedReverse: isAnimatedEVUReverse }]"
              style="fill:none;fill-rule:evenodd;stroke:white;stroke-width:0.75;stroke-linecap:butt;stroke-linejoin:miter;stroke-miterlimit:4;"
              d="M 40,20 85,60" id="evu-line" inkscape:connector-type="polyline" inkscape:connector-curvature="0"
              inkscape:connection-start="#path846" inkscape:connection-end="#path1109" />
            <path :class="{ animated: isAnimatedPV }"
              style="fill:none;fill-rule:evenodd;stroke:grey;stroke-width:0.75;stroke-linecap:butt;stroke-linejoin:miter;stroke-miterlimit:4;"
              d="M 130,20 85,60" id="pv-line" inkscape:connector-type="polyline" inkscape:connector-curvature="0"
              inkscape:connection-start="#path846-2" inkscape:connection-end="#path1109" />
            <path :class="{ animatedReverse: isAnimatedHome }"
              style="fill:none;fill-rule:evenodd;stroke:gray;stroke-width:0.75;stroke-linecap:butt;stroke-linejoin:miter;stroke-miterlimit:4;"
              d="M 40,60 85,60" id="home-line" inkscape:connector-type="polyline" inkscape:connector-curvature="0"
              inkscape:connection-start="#path846-6" inkscape:connection-end="#path1109" />
            <path :class="[{ animatedReverse: isAnimatedBattery }, { animated: isAnimatedBatteryReverse }]"
              style="fill:none;fill-rule:evenodd;stroke:gray;stroke-width:0.75;stroke-linecap:butt;stroke-linejoin:miter;stroke-miterlimit:4;"
              d="M 130,60 85,60" id="battery-line" inkscape:connector-type="polyline" inkscape:connector-curvature="0"
              inkscape:connection-start="#path846-6-9" inkscape:connection-end="#path1109" />
            <path :class="{ animatedReverse: isAnimatedCharge1 }"
              style="fill:none;fill-rule:evenodd;stroke:gray;stroke-width:0.75;stroke-linecap:butt;stroke-linejoin:miter;stroke-miterlimit:4;"
              d="M 40,100 85,60" id="L1-line" inkscape:connector-type="polyline" inkscape:connector-curvature="0"
              inkscape:connection-start="#path846-5" inkscape:connection-end="#path1109" />
            <path :class="{ animatedReverse: isAnimatedCharge2 }"
              style="fill:none;fill-rule:evenodd;stroke:gray;stroke-width:0.75;stroke-linecap:butt;stroke-linejoin:miter;stroke-miterlimit:4;"
              d="M 130,100 85,60" id="L2-line" inkscape:connector-type="polyline" inkscape:connector-curvature="0"
              inkscape:connection-start="#path846-5-1" inkscape:connection-end="#path1109" />
            <g id="g18913">
              <circle
                style="fill:black;fill-opacity:1;stroke:gray;stroke-width:0.75;stroke-miterlimit:2;stroke-opacity:1"
                id="evu" cx="40" cy="20" r="10" />
              <image href="/icons/owbEVU.svg" x="32.5" y="12" height="15px" width="15px" />
              <circle
                style="display:inline;fill:black;fill-opacity:1;stroke:gray;stroke-width:0.75;stroke-miterlimit:2;stroke-opacity:1"
                id="home" cx="40" cy="60" r="10" />
              <image href="/icons/owbHouse.svg" x="34.5" y="55" height="11px" width="11px" />
              <circle
                style="display:inline;fill:black;fill-opacity:1;stroke:gray;stroke-width:0.75;stroke-miterlimit:2;stroke-opacity:1"
                id="L1" cx="40" cy="100" r="10" />
              <image href="/icons/owbCharge.svg" x="35.5" y="95.5" height="9px" width="9px" />
            </g>
            <g id="g18908">
              <circle
                style="fill:Black;fill-opacity:1;stroke:gray;stroke-width:0.75;stroke-miterlimit:2;stroke-opacity:1"
                id="pv" cx="130" cy="20" r="10" />
              <image href="/icons/owbPV.svg" x="124" y="13" height="12px" width="12px" />
              <circle
                style="display:inline;fill:black;fill-opacity:1;stroke:gray;stroke-width:0.75;stroke-miterlimit:2;stroke-opacity:1"
                id="battery" cx="130" cy="60" r="10" />
              <image href="/icons/owbBattery.svg" x="124.5" y="55" height="11px" width="11px" />
              <circle
                style="display:inline;fill:black;fill-opacity:1;stroke:gray;stroke-width:0.75;stroke-miterlimit:2;stroke-opacity:1"
                id="L2" cx="130" cy="100" r="10" />
              <image href="/icons/owbCharge.svg" x="126" y="95.5" height="9px" width="9px" />
            </g>
            <circle style="fill:gray;fill-opacity:1;stroke-width:0.5;stroke-miterlimit:2" id="center" cx="85"
              cy="60" r="2" />

            <text xml:space="preserve"
              style="font-style:normal;font-weight:normal;font-size:5px;line-height:1.25;font-family:Arial;fill:#000000;fill-opacity:1;stroke:none;stroke-width:0.264583"
              id="EVU" text-anchor="end">
              <tspan sodipodi:role="line" style="fill:white;fill-opacity:1;stroke-width:0.264583" x="26" y="19">EVU</tspan>
              <tspan sodipodi:role="line" :class="{ text_green: !EVUPositive, text_red: EVUPositive }"
                style="fill:white;fill-opacity:1;stroke-width:0.264583" x="26" y="25">{{ this.gridPower.textValue }}
              </tspan>
            </text>

            <text xml:space="preserve"
              style="font-style:normal;font-weight:normal;font-size:5px;line-height:1.25;font-family:Arial;fill:#000000;fill-opacity:1;stroke:none;stroke-width:0.264583"
              id="PV" text-anchor="start">
              <tspan sodipodi:role="line" style="fill:white;fill-opacity:1;stroke-width:0.264583" x="144" y="19">PV</tspan>
              <tspan sodipodi:role="line" :class="{ text_green: PVPositive }"
                style="fill:white;fill-opacity:1;stroke-width:0.264583" x="144" y="25">{{ this.pvPower.textValue }}
              </tspan>
            </text>

            <text xml:space="preserve"
              style="font-style:normal;font-weight:normal;font-size:5px;line-height:1.25;font-family:Arial;fill:#000000;fill-opacity:1;stroke:none;stroke-width:0.264583"
              id="Home" text-anchor="end">
              <tspan sodipodi:role="line" style="fill:white;fill-opacity:1;stroke-width:0.264583" x="26" y="60">Haus</tspan>
              <tspan sodipodi:role="line" :class="{ text_green: HomePositive }"
                style="fill:white;fill-opacity:1;stroke-width:0.264583" x="26" y="66">{{ this.homePower.textValue }}
              </tspan>
            </text>

            <text xml:space="preserve"
              style="font-style:normal;font-weight:normal;font-size:5px;line-height:1.25;font-family:Arial;fill:#000000;fill-opacity:1;stroke:none;stroke-width:0.264583"
              id="Battery" text-anchor="start">
              <tspan sodipodi:role="line" style="fill:white;fill-opacity:1;stroke-width:0.264583" x="144" y="60">Speicher</tspan>
              <tspan sodipodi:role="line" :class="batteryClass" style="fill:white;fill-opacity:1;stroke-width:0.264583"
                x="144" y="66">{{ this.batteryPower.textValue }}</tspan>
            </text>

            <text xml:space="preserve"
              style="font-style:normal;font-weight:normal;font-size:5px;line-height:1.25;font-family:Arial;fill:#000000;fill-opacity:1;stroke:none;stroke-width:0.264583"
              id="LP1" text-anchor="end">
              <tspan sodipodi:role="line" style="fill:white;fill-opacity:1;stroke-width:0.264583"
                x="26" y="100">Ladepunkt1</tspan>
              <tspan sodipodi:role="line" :class="{ text_green: LP1Positive }"
                style="fill:white;fill-opacity:1;stroke-width:0.264583" x="26" y="106">{{
                  this.chargePoint1Power.textValue
                }}</tspan>
            </text>

            <text xml:space="preserve"
              style="font-style:normal;font-weight:normal;font-size:5px;line-height:1.25;font-family:Arial;fill:#000000;fill-opacity:1;stroke:none;stroke-width:0.264583"
              id="LP2" text-anchor="start">
              <tspan sodipodi:role="line" style="fill:white;fill-opacity:1;stroke-width:0.264583"
                x="144" y="100">Ladepunkt2</tspan>
              <tspan sodipodi:role="line" :class="{ text_green: LP2Positive }"
                style="fill:white;fill-opacity:1;stroke-width:0.264583" x="144" y="106">{{
                  this.chargePoint2Power.textValue
                }}</tspan>
            </text>
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

#diagram path {
  transition: stroke 0.5s;
}

#diagram path.animated {
  stroke: green !important;
  stroke-dasharray: 5;
  animation: dash 1s linear infinite;
}

#diagram path.animatedReverse {
  stroke: green !important;
  stroke-dasharray: 5;
  animation: dashReverse 1s linear infinite;
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

.text_green {
  fill: green !important;
  /* or any color you prefer for positive values */
}

.text_red {
  fill: red !important;
  /* or any color you prefer for negative values */
}
</style>