<script>
import { useMqttStore } from "@/stores/mqtt.js";

export default {
  name: "DashboardSimpleView",
  props: {
    changesLocked: { required: false, type: Boolean, default: false },
  },
  data() {
    return {
      mqttStore: useMqttStore(),
      isAnimatingEVU: false,
      isAnimatingPV: false,
      isAnimatingHouse: false,
      isAnimatingBattery: false,
      isAnimatingCharger_1: false,
      isAnimatingCharger_2: false,

      batteryAnimationDirection: '',
    };
  },
  computed: {
    gridPower() {
      return parseFloat(this.mqttStore.getGridPower.replace('W', '').replace(',', ''));
    },
    pvPower() {
      return parseFloat(this.mqttStore.getPvPower.replace('W', '').replace(',', ''));
    },
    homePower() {
      return parseFloat(this.mqttStore.getHomePower.replace('W', '').replace(',', ''));
    },
    batteryPower() {
      return parseFloat(this.mqttStore.getBatteryPower.replace('W', '').replace(',', ''));
    },
    //Charge point id's may vary in the setup ..need method of confirmig them as LP 1 and LP 2
    chargePoint1Power() {
      return parseFloat(this.mqttStore.getChargePointPower(2).replace('W', '').replace(',', ''));
    },
    chargePoint2Power() {
      return parseFloat(this.mqttStore.getChargePointPower(3).replace('W', '').replace(',', ''));
    }
  },
  methods: {
    animationDirection(){
      if(this.pvPower > 80){
        this.isAnimatingPV = true;
      } else {
        this.isAnimatingPV = false;
      }

      if(this.gridPower > 0){
        this.isAnimatingEVU = true;
      } else {
        this.isAnimatingEVU = false;
      }

      if (this.batteryPower > 0) {
        this.isAnimatingBattery = true;
        this.batteryAnimationDirection = 'right';
        
      } else if (this.batteryPower < 0) {
        this.isAnimatingBattery = true;
        this.batteryAnimationDirection = 'left';
        
      } else {
        this.isAnimatingBattery = false;
        this.batteryAnimationDirection = null;
      }

      if(this.homePower > 0){
        this.isAnimatingHouse = true;
      } else {
        this.isAnimatingHouse = false;
      }

      if(this.chargePoint1Power > 0){
        this.isAnimatingCharger_1 = true;
      } else {
        this.isAnimatingCharger_1 = false;
      }

      if(this.chargePoint2Power > 0){
        this.isAnimatingCharger_2 = true;
      } else {
        this.isAnimatingCharger_2 = false;
      }
    
    },
  },
  watch:{
    gridPower: 'animationDirection',
    pvPower: 'animationDirection',
    homePower: 'animationDirection',
    batteryPower: 'animationDirection',
    chargePoint1Power: 'animationDirection',
    chargePoint2Power: 'animationDirection'
  },
  mounted(){
    this.animationDirection();
  },
};
</script>

<template>
  <div class="diagram-container">
    <div id="bd-1" :class="['base-div', 'base-top-left', 'padding-top-20', { 'animate-arrow-right': isAnimatingEVU },{ 'animate-arrow-left': !isAnimatingEVU} ]">
        <div class="flex-column-left text-width">
          <span class="power-text">{{ mqttStore.getGridPower }}</span>
          <span class="component-text">EVU</span>
        </div>
      <div class="component-EVU flex-center">
        <img src="/icons/owbEVU.svg" style="width: 3.5em; height: 3.5em;">
      </div>
      <span class="text-width"></span>
    </div>

    <div id="bd-2" :class="['base-div', 'base-top-right', 'padding-top-20', { 'animate-arrow-left': isAnimatingPV }]">
      <span class="text-width"></span>
      <div class="component-PV flex-center">
        <img src="/icons/owbPV.svg" style="width: 2.5em; height: 2.5em;">
      </div>
      <div class="flex-column-right text-width">
          <span class="power-text">{{ mqttStore.getPvPower }}</span>
          <span class="component-text">PV</span>
        </div>
            <!-- Div created as reference for verical line joining house-battery to charging points -->
            <div id="center-div" :class="['center-div-top',{'animate-arrow-left': isAnimatingHouse || isAnimatingBattery } ]">
          <div class="center-content"></div>
        </div>
    </div>

    <div id="bd-3" :class="['base-div', 'middle-bottom-left', {'animate-arrow-left': isAnimatingHouse} ]">
      <div class="flex-column-left text-width">
          <span class="power-text">{{ mqttStore.getHomePower }}</span>
          <span class="component-text">Haus</span>
        </div>
      <div class="component-EVU flex-center">
        <img src="/icons/owbHouse.svg" style="width: 2.5em; height: 2.5em;">
      </div>
      <span class="text-width"></span>
    </div>

    <div id="bd-4" :class="['base-div', 'middle-bottom-right', { 'animate-arrow-right': isAnimatingBattery && batteryAnimationDirection === 'right' }, 
                                                        { 'animate-arrow-left': isAnimatingBattery && batteryAnimationDirection === 'left' },
                                                        { 'no-animation': batteryAnimationDirection === null }]">
      <span class="text-width"></span>
      <div class="component-PV flex-center">
        <img src="/icons/owbBattery.svg" style="width: 2.5em; height: 2.5em;">
      </div>
      <div class="flex-column-right text-width">
          <span class="power-text">{{ mqttStore.getBatteryPower }}</span>
          <span class="component-text">Speicher</span>
        </div>
            <!-- Div created as reference for verical line joining house-battery to charging points -->
        <div id="center-div" :class="['center-div',{'animate-arrow-left': isAnimatingCharger_1 || isAnimatingCharger_2 } ]">
          <div class="center-content"></div>
        </div>
    </div>

    <div id="bd-5" :class="['base-div', 'middle-bottom-left', {'animate-arrow-left': isAnimatingCharger_1}]">
      <div class="flex-column-left text-width">
          <span class="power-text">{{mqttStore.getChargePointPower(2)}}</span>
          <span class="component-text">Ladepunkt-1</span>
        </div>
      <div class="component-EVU flex-center">
        <img src="/icons/owbCharge.svg" style="width: 2em; height: 2em;">
      </div>
      <span class="text-width"></span>
    </div>

    <div id="bd-6" :class="['base-div', 'middle-bottom-right',{'animate-arrow-right': isAnimatingCharger_2}]">
      <span class="text-width"></span>
      <div class="component-PV flex-center">
        <img src="/icons/owbCharge.svg" style="width: 2em; height: 2em;">
      </div>
      <div class="flex-column-right text-width">
          <span class="power-text">{{mqttStore.getChargePointPower(3)}}</span>
          <span class="component-text">Ladepunkt-2</span>
        </div>
    </div>
  </div>
</template>

<style scoped>
/* Keyframes for the animation moving to the right */
@keyframes arrow-animation-right {
  0% {
    background-position: 100% 50%;
  }
  100% {
    background-position: 0 50%;
  }
}

/* Keyframes for the animation moving to the left */
@keyframes arrow-animation-left {
  0% {
    background-position: 0 50%;
  }
  100% {
    background-position: 100% 50%;
  }
}

/* Diagram container styling */
.diagram-container {
  display: flex;
  flex-wrap: wrap;
  height: 400px;
  width: 100%;
  margin-top: 0.5rem;
  background-color: #46444c;
  color: white;
  border-radius: 5px;
}

/* Base div styling */
.base-div {
  height: 33.3%;
  width: 50%;
  display: flex;
  flex-wrap: wrap;
  background-color: transparent;
  position: relative; /* Ensure pseudo-elements are positioned correctly */
}

/* Styling for top-left and top-right base divs */
.base-top-left,
.base-top-right {
  display: flex;
  justify-content: center;
  position: relative;
}

/* Default state for pseudo-elements (lines) TOP -- EVU and PV*/
.base-top-left::after,
.base-top-right::after {
  content: "";
  position: absolute;
  background: white;
  width: 50%; /* Horizontal line */
  height: 2px;
  bottom: 0;
}

.base-top-left::after {
  right: 0; /* Horizontal alignment */
}

.base-top-right::after {
  left: 0; /* Horizontal alignment */
}

.base-top-left::before,
.base-top-right::before {
  content: "";
  position: absolute;
  background: white;
  width: 2px; /* Vertical line */
  height: 50%;
  bottom: 0;
  right: 50%;
}

/* Centered reference div placed so that a line can connect EVU and PV to Home and battery */
.center-div-top {
  position: absolute;
  bottom: -50%; 
  left: 0; /* Horizontal alignment */
  background-color: #0c0b0e;
  min-width: 0px;
  height: 50%; /* Line length relative to div*/
  z-index: 10; 
}

.center-div-top::before {
  content: "";
  position: absolute;
  background: white;
  width: 2px; /* Vertical line */
  height: 100%; /* Line length relative to div*/
  bottom: 0; /* Vertical alignment */
  left: -1px;
}

/* Styling for MIDDLE and BOTTOM base divs */
.middle-bottom-left,
.middle-bottom-right {
  display: flex;
  justify-content: center;
  position: relative;
  align-content: center;
}

.middle-bottom-left::before{
  right: -1px; /* Horizontal alignment */
}

.middle-bottom-right::before{
  left: -1px; /* Horizontal alignment */
}

.middle-bottom-left::after,
.middle-bottom-right::after  {
  content: "";
  position: absolute;
  background: white;
  width: 50%; /* Horizontal line */
  height: 2px;
  top: 50%;
}

.middle-bottom-left::after {
  right: 0; /* Horizontal alignment */
}

.middle-bottom-right::after {
  left: 0; /* Horizontal alignment */
}

/* Centered reference div placed so that a line can connect house and battery to charge points */
.center-div {
  position: absolute;
  top: 50%; /* Center vertically within the container */
  left: 0; /* Center horizontally within the container */
  min-width: 0px;
  height: 100%;
  z-index: 1;
}

/* Seperate vertical line to charge points */
.center-div::before {
  content: "";
  position: absolute;
  background: white;
  width: 2px; /* Vertical line */
  height: 100%;
  bottom: 0;
  left: -1px;
}

/* Conditional animation and visibility for (animation moving to the right) TOP*/
.animate-arrow-right::before,
.animate-arrow-right::after {
  background: repeating-linear-gradient(
    135deg,
    transparent,
    transparent 10px,
    green 15px,
    green 30px
  );
  background-size: 200% 100%;
  animation: arrow-animation-right 1.5s infinite linear;
}

/* Conditional animation and visibility for (animation moving to the left) TOP*/
.animate-arrow-left::before,
.animate-arrow-left::after {
  background: repeating-linear-gradient(
    135deg,
    transparent,
    transparent 10px,
    green 15px,
    green 30px
  );
  background-size: 200% 100%;
  animation: arrow-animation-left 1.5s infinite linear;
}

/* No animation state */
.no-animation::before,
.no-animation::after {
  animation: none;
}

.flex-center {
  display: flex;
  justify-content: center;
  align-items: center;
}

/* Component styling */
.component-EVU,
.component-PV {
  height: 70px;
  width: 70px;
  border-radius: 50%;
  background-color: #222;
  border: 2px solid white;
  z-index: 1;
}

.text-width {
  width: 120px;
  padding-top: 20px;
}

.flex-column-left {
  display: flex;
  flex-direction: column;
  align-items: flex-end;
  padding-right: 10px
}

.flex-column-right {
  display: flex;
  flex-direction: column;
  align-items: flex-start;
  padding-left: 10px;
}

.power-text {
  font-weight: 700;
}

.component-text {
  font-weight: 700;
  color: #c9a68f;
}

.padding-top-20 {
  padding-top: 20px;  
}
</style>
