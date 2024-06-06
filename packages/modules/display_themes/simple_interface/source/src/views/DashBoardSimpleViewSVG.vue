<script>
import { useMqttStore } from "@/stores/mqtt.js";
import DashBoardCard from "@/components/DashBoardCard.vue";

export default {
  name: "DashboardCanvasViewSVG",
  components: {
    DashBoardCard,
  },
  props: {
    changesLocked: { required: false, type: Boolean, default: false },
  },
  data() {
    return {
      isAnimatedEVU: false,
      isAnimatedEVUReverse: false,
      isAnimatedPV: false,
      isAnimatedPVReverse: false,
      isAnimatedHome: false,
      isAnimatedBattery: false,
      isAnimatedBatteryReverse: false,
      isAnimatedCharge1: false,
      isAnimatedCharge2: false,

      EVUPositive: false,
      PVPositive: false,
      HomePositive: false,
      
      BatteryPositive: false,
      


      
      mqttStore: useMqttStore(),
      images: {
        evu: new Image(),
        pv: new Image(),
        house: new Image(),
        battery: new Image(),
        charge: new Image(),
      },
    };
  },
  computed: {
    gridPower() {
      return parseFloat(this.mqttStore.getGridPower.replace("W", "").replace(",", ""));
    },
    pvPower() {
      return parseFloat(this.mqttStore.getPvPower.replace("W", "").replace(",", ""));
    },
    homePower() {
      return parseFloat(this.mqttStore.getHomePower.replace("W", "").replace(",", ""));
    },
    batteryPower() {
      return parseFloat(this.mqttStore.getBatteryPower.replace("W", "").replace(",", ""));
    },
    chargePoint1Power() {
      return parseFloat(this.mqttStore.getChargePointPower(2).replace("W", "").replace(",", ""));
    },
    chargePoint2Power() {
      return parseFloat(this.mqttStore.getChargePointPower(3).replace("W", "").replace(",", ""));
    },
  },
  watch: {
    gridPower: 'energyFlow',
    pvPower: 'energyFlow',
    },
  methods: {
    energyFlow(){
      if(this.gridPower > 0){
        this.isAnimatedEVU = true;
        this.isAnimatedEVUReverse = false;
        this.EVUPositive = true;
      } else {
        this.isAnimatedEVU = false;
        this.isAnimatedEVUReverse = true;
        this.EVUPositive = false;
      }
      console.log(this.EVUNegitive)

      if(this.pvPower > 100){
        this.isAnimatedPV = true;
        this.PVPositive = true;
      } else {
        this.isAnimatedPV = false;
        this.PVPositive = false;
      }

      if(this.homePower > 0){
        this.isAnimatedHome = true;
        this.HomePositive = true;
      } else {
        this.HomePositive = false;
      }

      if(this.batteryPower < 0){
        this.isAnimatedBattery = true;
        this.isAnimatedBatteryReverse = false;
        this.BatteryPositive = false;
      } else if (this.batteryPower > 0){
        this.isAnimatedBattery = false;
        this.isAnimatedBatteryReverse = true;
        this.BatteryPositive = true;
      } else if (this.batteryPower == 0) {
        this.isAnimatedBattery = false;
        this.isAnimatedBatteryReverse = false;
      }

      if(this.chargePoint1Power > 0){
        this.isAnimatedCharge1 = true;
      } else {
        this.isAnimatedCharge1 = false;
      }
      
      if(this.chargePoint2Power > 0){
        this.isAnimatedCharge2 = true;
      } else {
        this.isAnimatedCharge2 = false;
      }
    },
  },
  mounted() {
    this.images.evu.src = './icons/owbEVU.svg';
    this.images.pv.src = './icons/owbPV.svg';
    this.images.house.src = './icons/owbHouse.svg';
    this.images.battery.src = './icons/owbBattery.svg';
    this.images.charge.src = './icons/owbCharge.svg';
    this.images.charge.onload = () => {
      this.energyFlow();
    };
  },
};
</script>

<template>
  <dash-board-card color="primary">
    <template #headerLeft> Übersicht - Energiefluss </template>
    <i-container>
      <div class="svg-container">
        <svg
    width="600"
    height="400"
    viewBox="0 0 170.09999 121.70834"
    version="1.1"
    id="svg5"
    xmlns="http://www.w3.org/2000/svg"
    xmlns:svg="http://www.w3.org/2000/svg">
    <defs id="defs2" />
    <g inkscape:label="Ebene 1" inkscape:groupmode="layer" id="layer1" style="display:inline">
        <path
            :class="[{ animated: isAnimatedEVU }, { animatedReverse: isAnimatedEVUReverse }]"
            style="fill:none;fill-rule:evenodd;stroke:white;stroke-width:0.264583;stroke-linecap:butt;stroke-linejoin:miter;stroke-miterlimit:4;"
            d="M 40,20 85,60"
            id="evu-line"
            inkscape:connector-type="polyline"
            inkscape:connector-curvature="0"
            inkscape:connection-start="#path846"
            inkscape:connection-end="#path1109" />
        <path
            :class="[{ animated: isAnimatedPV }, { animatedReverse: isAnimatedPVReverse }]"
            style="fill:none;fill-rule:evenodd;stroke:white;stroke-width:0.264583;stroke-linecap:butt;stroke-linejoin:miter;stroke-miterlimit:4;"
            d="M 130,20 85,60"
            id="pv-line"
            inkscape:connector-type="polyline"
            inkscape:connector-curvature="0"
            inkscape:connection-start="#path846-2"
            inkscape:connection-end="#path1109" />
        <path
            :class="{ animatedReverse: isAnimatedHome}"
            style="fill:none;fill-rule:evenodd;stroke:white;stroke-width:0.265;stroke-linecap:butt;stroke-linejoin:miter;stroke-miterlimit:4;"
            d="M 40,60 85,60"
            id="home-line"
            inkscape:connector-type="polyline"
            inkscape:connector-curvature="0"
            inkscape:connection-start="#path846-6"
            inkscape:connection-end="#path1109" />
        <path
            :class="[{ animated: isAnimatedBattery }, { animatedReverse: isAnimatedBatteryReverse }]"
            style="fill:none;fill-rule:evenodd;stroke:white;stroke-width:0.265;stroke-linecap:butt;stroke-linejoin:miter;stroke-miterlimit:4;"
            d="M 130,60 85,60"
            id="battery-line"
            inkscape:connector-type="polyline"
            inkscape:connector-curvature="0"
            inkscape:connection-start="#path846-6-9"
            inkscape:connection-end="#path1109" />
        <path
            :class="{ animatedReverse: isAnimatedCharge1 }"
            style="fill:none;fill-rule:evenodd;stroke:white;stroke-width:0.264583;stroke-linecap:butt;stroke-linejoin:miter;stroke-miterlimit:4;"
            d="M 40,100 85,60"
            id="L1-line"
            inkscape:connector-type="polyline"
            inkscape:connector-curvature="0"
            inkscape:connection-start="#path846-5"
            inkscape:connection-end="#path1109" />
        <path
            :class="{ animatedReverse: isAnimatedCharge2 }"
            style="fill:none;fill-rule:evenodd;stroke:white;stroke-width:0.265;stroke-linecap:butt;stroke-linejoin:miter;stroke-miterlimit:4;"
            d="M 130,100 85,60"
            id="L2-line"
            inkscape:connector-type="polyline"
            inkscape:connector-curvature="0"
            inkscape:connection-start="#path846-5-1"
            inkscape:connection-end="#path1109" />
        <g id="g18913">
            <circle
                style="fill:black;fill-opacity:1;stroke:white;stroke-width:0.529167;stroke-miterlimit:2;stroke-opacity:0.503672"
                id="evu"
                cx="40"
                cy="20"
                r="10" />
            <image
                :href="images.evu.src"
                x="32.5"
                y="12"
                height="15px"
                width="15px" />
            <circle
                style="display:inline;fill:black;fill-opacity:1;stroke:white;stroke-width:0.529167;stroke-miterlimit:2;stroke-opacity:0.499367"
                id="home"
                cx="40"
                cy="60"
                r="10" />
            <image
                :href="images.house.src"
                x="34.5"
                y="55"
                height="11px"
                width="11px" />
            <circle
                style="display:inline;fill:black;fill-opacity:1;stroke:white;stroke-width:0.529167;stroke-miterlimit:2;stroke-opacity:0.501961"
                id="L1"
                cx="40"
                cy="100"
                r="10" />
            <image
                :href="images.charge.src"
                x="35.5"
                y="95.5"
                height="9px"
                width="9px" />
        </g>
        <g id="g18908">
            <circle
                style="fill:Black;fill-opacity:1;stroke:white;stroke-width:0.529167;stroke-miterlimit:2;stroke-opacity:0.496088"
                id="pv"
                cx="130"
                cy="20"
                r="10" />
            <image
                :href="images.pv.src"
                x="124"
                y="13"
                height="12px"
                width="12px" />
            <circle
                style="display:inline;fill:black;fill-opacity:1;stroke:white;stroke-width:0.529167;stroke-miterlimit:2;stroke-opacity:0.501662"
                id="battery"
                cx="130"
                cy="60"
                r="10" />
            <image
                :href="images.battery.src"
                x="124.5"
                y="55"
                height="11px"
                width="11px" />
            <circle
                style="display:inline;fill:black;fill-opacity:1;stroke:white;stroke-width:0.529167;stroke-miterlimit:2;stroke-opacity:0.501961"
                id="L2"
                cx="130"
                cy="100"
                r="10" />
            <image
                :href="images.charge.src"
                x="126"
                y="95.5"
                height="9px"
                width="9px" />
        </g>
        <circle
            style="fill:gray;fill-opacity:1;stroke-width:0.529167;stroke-miterlimit:2"
            id="center"
            cx="85"
            cy="60"
            r="2" />

        <text  
        xml:space="preserve"
        style="font-style:normal;font-weight:normal;font-size:5px;line-height:1.25;font-family:Arial;fill:#000000;fill-opacity:1;stroke:none;stroke-width:0.264583"
        id="EVU"
        text-anchor="end">
        <tspan
        sodipodi:role="line"
        style="fill:white;fill-opacity:1;stroke-width:0.264583"
        x="26"
        y="19">EVU</tspan>
        <tspan
        sodipodi:role="line"
        :class="{text_green: !EVUPositive, text_red: EVUPositive}"
        style="fill:white;fill-opacity:1;stroke-width:0.264583"
        x="26"
        y="25">{{ this.gridPower }} W</tspan>
        </text>

        <text  
        xml:space="preserve"
        style="font-style:normal;font-weight:normal;font-size:5px;line-height:1.25;font-family:Arial;fill:#000000;fill-opacity:1;stroke:none;stroke-width:0.264583"
        id="PV"
        text-anchor="start">
        <tspan
        sodipodi:role="line"
        style="fill:white;fill-opacity:1;stroke-width:0.264583"
        x="145"
        y="19">PV</tspan>
        <tspan
        sodipodi:role="line"
        :class="{text_green: PVPositive}"
        style="fill:white;fill-opacity:1;stroke-width:0.264583"
        x="145"
        y="25">{{ this.pvPower }} W</tspan>
        </text>
        
        <text  
        xml:space="preserve"
        style="font-style:normal;font-weight:normal;font-size:5px;line-height:1.25;font-family:Arial;fill:#000000;fill-opacity:1;stroke:none;stroke-width:0.264583"
        id="Home"
        text-anchor="end">
        <tspan
        sodipodi:role="line"
        style="fill:white;fill-opacity:1;stroke-width:0.264583"
        x="26"
        y="60">Haus</tspan>
        <tspan
        sodipodi:role="line"
        :class="{text_green: HomePositive}"
        style="fill:white;fill-opacity:1;stroke-width:0.264583"
        x="26"
        y="66">{{ this.homePower }} W</tspan>
        </text> 

        <text  
        xml:space="preserve"
        style="font-style:normal;font-weight:normal;font-size:5px;line-height:1.25;font-family:Arial;fill:#000000;fill-opacity:1;stroke:none;stroke-width:0.264583"
        id="Battery"
        text-anchor="start">
        <tspan
        sodipodi:role="line"
        style="fill:white;fill-opacity:1;stroke-width:0.264583"
        x="145"
        y="60">Speicher</tspan>
        <tspan
        sodipodi:role="line"
        :class="{text_green: !BatteryPositive, text_red: BatteryPositive}"
        style="fill:white;fill-opacity:1;stroke-width:0.264583"
        x="145"
        y="66">{{ this.gridPower }} W</tspan>
        </text>

        <text
        xml:space="preserve"
        style="font-style:normal;font-weight:normal;font-size:5px;line-height:1.25;font-family:Arial;fill:#000000;fill-opacity:1;stroke:none;stroke-width:0.264583"
        id="LP1"
        text-anchor="end">
        <tspan
        sodipodi:role="line"
        id="tspan-label"
        style="fill:white;fill-opacity:1;stroke-width:0.264583"
        x="26"
        y="100">Ladepunkt1</tspan>
        <tspan
        sodipodi:role="line"
        :class="{text_green: BatteryPositive}"
        style="fill:white;fill-opacity:1;stroke-width:0.264583"
        x="26"
        y="106">{{ this.chargePoint1Power }}</tspan>
        </text>

        <text
        xml:space="preserve"
        style="font-style:normal;font-weight:normal;font-size:5px;line-height:1.25;font-family:Arial;fill:#000000;fill-opacity:1;stroke:none;stroke-width:0.264583"
        id="LP2"
        text-anchor="start">
        <tspan
        sodipodi:role="line"
        id="tspan-label"
        style="fill:white;fill-opacity:1;stroke-width:0.264583"
        x="145"
        y="100">Ladepunkt2</tspan>
        <tspan
        sodipodi:role="line"
        :class="{text_green: BatteryPositive}"
        style="fill:white;fill-opacity:1;stroke-width:0.264583"
        x="145"
        y="106">{{ this.chargePoint2Power }}</tspan>
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

#svg5 path {
  transition: stroke 0.5s;
}

#svg5 path.animated {
  stroke: green !important;
  stroke-dasharray: 5;
  animation: dash 1s linear infinite;
}

#svg5 path.animatedReverse {
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
    fill: green !important; /* or any color you prefer for positive values */
}

.text_red {
    fill: red !important; /* or any color you prefer for negative values */
}
</style>