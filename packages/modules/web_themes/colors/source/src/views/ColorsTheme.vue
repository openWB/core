/* * ColorsTheme.vue * colors theme for openwb 2.0 * Copyright (c) 2022 Claus
Hagen */

<template>
  <div class="container-fluid px-2 m-0 theme-colors">
    <!-- Theme settings -->
    <div class="collapse" id="themesettings">
      <ThemeSettings></ThemeSettings>
    </div>
    <!-- Button Bar -->
    <ButtonBar></ButtonBar>

    <!-- Main Widgets -->
    <div class="row py-0 px-0 m-0" v-if="false">
      <PowerMeter></PowerMeter>
      <PowerGraph></PowerGraph>
      <EnergyMeter :usageDetails="usageDetails"></EnergyMeter>
    </div>
    <div class="row py-0 px-0 m-0" v-if="true">
      <Carousel>
        <template #item1>
          <PowerMeter></PowerMeter>
        </template>
        <template #item2>
          <PowerGraph></PowerGraph>
        </template>
        <template #item3>
          <EnergyMeter :usageDetails="usageDetails"></EnergyMeter>
        </template>
      </Carousel>
    </div>
    

    <!-- Detail configuration list -->
    <div
      class="row py-0 m-0 d-flex justify-content-center"
      v-if="!globalConfig.showQuickAccess"
    >
      <ChargePointList> </ChargePointList>
      <BatteryList> </BatteryList>
      <SmartHomeList> </SmartHomeList>
      <PriceChart> </PriceChart>
    </div>
    <!-- Tabbed area -->
    <nav
      class="nav nav-tabs nav-justified mx-1 mt-2"
      role="tablist"
      v-if="globalConfig.showQuickAccess"
    >
      <a class="nav-link active" data-bs-toggle="tab" data-bs-target="#showAll">
        <i class="fa-solid fa-lg fa-circle-info me-1"></i>
        <span class="d-none d-md-inline ms-2">Alles</span>
      </a>
      <a
        class="nav-link"
        data-bs-toggle="tab"
        data-bs-target="#chargepointlist"
      >
        <i class="fa-solid fa-lg fa-charging-station"></i>
        <span class="d-none d-md-inline ms-2">Ladepunkte</span>
      </a>
      <a
        class="nav-link"
        data-bs-toggle="tab"
        data-bs-target="#batterylist"
        v-if="globalData.isBatteryConfigured"
      >
        <i class="fa-solid fa-lg fa-car-battery"></i>
        <span class="d-none d-md-inline ms-2">Speicher</span>
      </a>
      <a class="nav-link" data-bs-toggle="tab" data-bs-target="#smarthomelist">
        <i class="fa-solid fa-lg fa-plug"></i>
        <span class="d-none d-md-inline ms-2">Smart Home</span>
      </a>
      <a
        class="nav-link"
        data-bs-toggle="tab"
        data-bs-target="#etPricing"
        v-if="etData.isEtEnabled"
      >
        <i class="fa-solid fa-lg fa-money-bill-1-wave"></i>
        <span class="d-none d-md-inline ms-2">Strompreis</span>
      </a>
    </nav>
    <!-- Tab panes -->
    <div
      class="tab-content mx-0 pt-1"
      id="cpContent"
      v-if="globalConfig.showQuickAccess"
    >
      <div
        class="tab-pane active"
        id="showAll"
        role="tabpanel"
        aria-labelledby="showall-tab"
      >
        <div class="row py-0 m-0 d-flex justify-content-center">
          <ChargePointList> </ChargePointList>
          <BatteryList> </BatteryList>
          <SmartHomeList> </SmartHomeList>
          <PriceChart> </PriceChart>
        </div>
      </div>
      <div
        class="tab-pane"
        id="chargepointlist"
        role="tabpanel"
        aria-labelledby="chargepoint-tab"
      >
        <div class="row py-0 m-0 d-flex justify-content-center">
          <ChargePointList> </ChargePointList>
        </div>
      </div>
      <div
        class="tab-pane"
        id="batterylist"
        role="tabpanel"
        aria-labelledby="battery-tab"
      >
        <div class="row py-0 m-0 d-flex justify-content-center">
          <BatteryList></BatteryList>
        </div>
      </div>
      <div
        class="tab-pane"
        id="smarthomelist"
        role="tabpanel"
        aria-labelledby="smarthome-tab"
      >
        <div class="row py-0 m-0 d-flex justify-content-center">
          <SmartHomeList></SmartHomeList>
        </div>
      </div>
      <div
        class="tab-pane"
        id="etPricing"
        role="tabpanel"
        aria-labelledby="pricechart-tab"
      >
        <div class="row py-0 m-0 d-flex justify-content-center">
          <PriceChart></PriceChart>
        </div>
      </div>
    </div>
  </div>
  <!-- Footer -->
  <div class="row p-2 mt-5">
    <div class="col p-2">
      <hr />
      <div class="d-flex justify-content-between">
        <p class="mx-4">Screen Width: {{ screensize.x }}</p>
   <!--      <button class="btn btn-sm btn-secondary mx-4" @click="toggleSetup">
          System Setup
        </button> -->
      <button class="btn btn-sm btn-secondary mx-4" @click="toggleMqViewer">
          MQ Viewer
        </button>
      </div>
    <!--   <hr v-if="showSetup" />
      <Setup v-if="showSetup"></Setup> -->
    
      <hr v-if="showMQ" />
      <MQTTViewer v-if="showMQ"></MQTTViewer>
    </div>
  </div>

    
</template>

<script setup lang="ts">
import { ref, reactive, computed, onMounted} from 'vue'
import { usageSummary, sourceSummary,shDevices, globalData,} from '../assets/js/model'
import { chargePoints } from '@/components/chargePointList/model'
import { etData } from '@/components/priceChart/model'
import { initConfig } from '@/assets/js/themeConfig'
import PowerMeter from '@/components/powerMeter/PowerMeter.vue'
import PowerGraph from '@/components/powerGraph/PowerGraph.vue'
import EnergyMeter from '@/components/energyMeter/EnergyMeter.vue'
import ChargePointList from '@/components/chargePointList/ChargePointList.vue'
import ButtonBar from '@/components/buttonBar/ButtonBar.vue'
import BatteryList from '@/components/batteryList/BatteryList.vue'
import PriceChart from '@/components/priceChart/PriceChart.vue'
import SmartHomeList from '@/components/smartHome/SmartHomeList.vue'
import Carousel from '@/components/shared/Carousel.vue'
import { msgInit } from '@/assets/js/processMessages'
import MQTTViewer from '@/components/mqttViewer/MQTTViewer.vue'
import Setup from '@/components/setup/Setup.vue'
import ModalComponent from "@/components/shared/ModalComponent.vue";
import ThemeSettings from "@/views/ThemeSettings.vue";
import { globalConfig, updateDimensions, screensize } from '@/assets/js/themeConfig'

// state
const usageDetails = computed(() => {
  return [usageSummary.evuOut, usageSummary.devices, usageSummary.charging]
    .concat(Object.values(chargePoints).map((cp) => cp.toPowerItem()))
    .concat(
      Object.values(shDevices).filter(
        (row) => row.configured && row.showInGraph,
      ),
    )
    .concat([usageSummary.batIn, usageSummary.house])
})
const showMQ = ref(false)
const showSetup = ref(false)
// methods
function init() {
  initConfig()
}
function toggleMqViewer() {
  showMQ.value = !showMQ.value
}
function toggleSetup() {
  showSetup.value = !showSetup.value
  console.log ("click")
}
function resetArcs() {
  let maxPower =
    sourceSummary.pv.power +
    sourceSummary.evuIn.power +
    sourceSummary.batOut.power;

    globalConfig.maxPower = maxPower
}
// lifecycle
onMounted(() => {
  init()
  window.addEventListener('resize', updateDimensions)
  msgInit()
})
</script>

<style scoped>
.nav-tabs {
  border-bottom: 0.5px solid var(--color-menu);
  background-color: var(--color-bg);
}
.nav-tabs .nav-link {
  color: var(--color-menu);
  opacity: 0.5;
}
.nav-tabs .nav-link.disabled {
  color: var(--color-axis);
  border: 0.5px solid var(--color-axis);
}

.nav-tabs .nav-link.active {
  color: var(--color-fg);
  background-color: var(--color-bg);
  opacity: 1;
  border: 0.5px solid var(--color-menu);
  border-bottom: 0px solid var(--color-menu);
  box-shadow: 0 0.5rem 1rem rgba(0, 0, 0, 0.15);
}
.fa-circle-info {
  color: var(--color-fg);
}
.fa-charging-station {
  color: var(--color-charging);
}
.fa-car-battery {
  color: var(--color-battery);
}
.fa-plug {
  color: var(--color-devices);
}
.fa-money-bill-1-wave {
  color: var(--color-pv);
}
</style>
