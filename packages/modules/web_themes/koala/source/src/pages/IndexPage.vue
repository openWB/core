<template>
  <q-page class="column">
    <!-- Top Carousel -->
    <div class="row justify-center full-width chart-section">
      <ChartCarousel />
    </div>

    <!-- Navigation Tabs -->
    <div class="tab-section">
      <q-tabs v-model="tab" dense class="q-tabs__content--align-justify">
        <q-tab name="charge-points" title="Ladepunkte">
          <q-icon name="ev_station" size="md" color="primary" />
        </q-tab>
        <q-tab name="vehicles" title="Fahrzeuge">
          <q-icon name="directions_car" size="md" color="primary" />
        </q-tab>
        <q-tab name="batteries" title="Speicher">
          <q-icon name="battery_full" size="md" color="primary" />
        </q-tab>
        <!-- <q-tab name="smart-home" title="SmartHome">
        <q-icon name="home" size="md" color="primary" />
      </q-tab> -->
      </q-tabs>
      <!-- Tab Panels -->
      <q-tab-panels v-model="tab" class="col">
        <!-- Charge Points -->
        <q-tab-panel name="charge-points" class="q-pa-none column">
          <ChargePointInformation />
        </q-tab-panel>
        <!-- Vehicles -->
        <q-tab-panel name="vehicles" class="q-pa-none column">
          <VehicleInformation />
        </q-tab-panel>
        <!-- Batteries -->
        <q-tab-panel name="batteries" class="remove-flex-properties">
          <BatteryInformation />
        </q-tab-panel>
        <!-- Smart Home -->
        <!-- <q-tab-panel name="smart-home" class="">
        <SmartHomeInformation />
      </q-tab-panel> -->
      </q-tab-panels>
    </div>
  </q-page>
</template>

<script setup lang="ts">
import { ref } from 'vue';
import ChartCarousel from 'src/components/ChartCarousel.vue';
import ChargePointInformation from 'src/components/ChargePointInformation.vue';
import BatteryInformation from 'src/components/BatteryInformation.vue';
import VehicleInformation from 'src/components/VehicleInformation.vue';
// import SmartHomeInformation from 'src/components/SmartHomeInformation.vue';

defineOptions({
  name: 'IndexPage',
});

const tab = ref<string>('charge-points');
</script>

<style scoped>
.chart-section {
  height: 40vh;
}
</style>
