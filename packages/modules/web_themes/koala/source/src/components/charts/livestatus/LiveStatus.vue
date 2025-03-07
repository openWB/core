<template>
    <div class="custom-width">
        <div class="card-container">
          <!-- PV Card -->
          <q-card v-if="hasPV" class="item pv" flat>
              <div class="header">PV</div>
              <div class="row">
                <div class="col text-value">
             {{ formatValue(pvPower*-1) }}W
                </div>
                <div class="col icon-container">
                  <q-badge rounded class="pv-background">
                    <q-icon name="solar_power" style="font-size: 24px;" class="pv-color" />
                    <q-tooltip class="bg-primary">Phasenanzahl</q-tooltip>
                  </q-badge>
                </div>
              </div>
          </q-card>
  
          <!-- Grid Card -->
          <q-card class="item grid" flat>
              <div class="header" >Netz</div>
              <div class="row">
                <div class="col text-value" >
                  {{ formatValue(gridPower) }}W
                </div>
                <div class="col icon-container">
                  <q-badge rounded class="grid-background">
                    <q-icon :name="mdiTransmissionTower" style="font-size: 24px;" class="grid-color"/>
                    <q-tooltip class="bg-primary">EVU</q-tooltip>
                  </q-badge>
                </div>
              </div>
  
          </q-card>
  
          <!-- House Card -->
          <q-card class="item house" flat>
              <div class="header" >Haus</div>
              <div class="row">
                <div class="col text-value">
                  {{ formatValue(homePower)}}W
                </div>
                <div class="col icon-container">
                  <q-badge rounded class="house-background">
                    <q-icon name="home" style="font-size: 24px;" class="house-color" />
                    <q-tooltip class="bg-primary">gesamter Hausverbrauch heute:<br></q-tooltip>
                  </q-badge>
                </div>
              </div>
          </q-card>
  
          <!-- Battery Card -->
          <q-card v-if="hasBattery" class="item battery" flat>
              <div class="header" >Speicher</div>
              <div class="row">
                <div class="col text-value" style="font-size: 14px;">
                  {{ formatValue(batteryPower) }}W<br />
                  {{ (batterySoc * 100).toFixed(0) }}%
                </div>
                <div class="col icon-container">
                  <q-badge rounded class="battery-background">
                    <q-icon name="battery_charging_full" style="font-size: 24px;" class="battery-color" />
                    <q-tooltip class="bg-primary">Speicher</q-tooltip>
                  </q-badge>
                </div>
              </div>
          </q-card>
  
          <!-- EV Card -->
          <q-card class="item ev" flat>
              <div class="header">Ladepunkte</div>
              <div class="row">
                <div class="col text-value">
                  {{ formatValue(evPower) }}W
                </div>
                <div class="col icon-container">
                  <q-badge rounded class="ev-background">
                    <q-icon name="ev_station" style="font-size: 24px;" class="ev-color" />
                    <q-tooltip class="bg-primary">Ladepunkte</q-tooltip>
                  </q-badge>
                </div>
              </div>
          </q-card>
        </div>
      
    </div>
  </template>
  
  <script setup lang="ts">
  import { onMounted, computed } from 'vue';
  import { QCard, QIcon } from 'quasar';
  import { useMqttStore } from 'src/stores/mqtt-store';
  import { mdiTransmissionTower} from '@mdi/js';
  
  const mqttStore = useMqttStore();
  
  const gridPower = computed(
    () => mqttStore.getGridPower('value') as number,
  );
  
  const hasBattery = computed( 
    () => mqttStore.batteryConfigured as boolean,
  );
  
  const hasPV = computed(
    () => mqttStore.getPvConfigured as boolean,
  );
  
  const batteryPower = computed(() => mqttStore.batteryTotalPower('value') as number);
  const batterySoc = computed(() => Number(mqttStore.batterySocTotal) / 100);
  const homePower = computed(
    () => mqttStore.getHomePower('value') as number,
  );
  const pvPower = computed(() => mqttStore.getPvPower('value') as number);
  const evPower = computed(() => mqttStore.chargePointSumPower('value') as number);
  
  const formatValue = (value: number) => {
    if (Math.abs(value) >= 1000) {
      return (value / 1000).toFixed(1) + 'k';
    }
    return value.toString();
  };
  
  onMounted(() => {
    //const interval = setInterval(fetchData, 5000);
    //onUnmounted(() => clearInterval(interval));
  });
  </script>
  
  <style scoped>
  .card-container {
    display: flex;
    flex-wrap: wrap;
    justify-content: space-around;
    gap: 10px;
  }
  
  .item {
    flex: 1 1 calc(50% - 20px); /* Adjust the width of the cards */
    display: flex;
    flex-direction: column;
    align-items: center;
    text-align: center;
    padding: 5px;
  }
  
  .item.pv {
    flex: 1 1 100%; /* Make the PV card span the entire row */
    border-left: 8px solid var(--pv-color); /* Add left border with pv-color */
  }
  
  .item.grid {
    border-left: 8px solid var(--grid-color);
  }
  
  .item.house {
    border-left: 8px solid var(--house-color);
  }
  
  .item.battery {
    border-left: 8px solid var(--battery-color);
  }
  
  .item.ev {
    border-left: 8px solid var(--ev-color);
  }
  
  .header {
    font-size: 14px;
    color: #888;
    text-align: left;
    width: 100%;
  }
  
  .row {
    display: flex;
    justify-content: space-between;
    align-items: center;
    width: 100%;
  }
  
  .text-value {
    font-size: 24px;
    font-weight: bold;
    text-align: left;
  }
  
  .icon-container {
    display: flex;
    justify-content: flex-end;
    align-items: center;
  }
  
  .q-icon {
    font-size: 20px;
  }
  
  .custom-width {
    width: 100%;
    max-width: 600px;
    margin: 0 auto; /* Center the card horizontally */
  }
  
  /* Define color classes */
  .pv-background {
    background-color: var(--pv-background);
  }
  
  .pv-color {
    color: var(--pv-color);
  }
  
  .grid-background {
    background-color: var(--grid-background);
  }
  
  .grid-color {
    color: var(--grid-color);
  }
  
  .house-background {
    background-color: var(--house-background);
  }
  
  .house-color {
    color: var(--house-color);
  }
  
  .battery-background {
    background-color: var(--battery-background);
  }
  
  .battery-color {
    color: var(--battery-color);
  }
  
  .ev-background {
    background-color: var(--ev-background);
  }
  
  .ev-color {
    color: var(--ev-color);
  }
  </style>