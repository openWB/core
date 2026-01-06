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
        <q-tab v-if="batteryAccessible" name="batteries" title="Speicher">
          <q-icon name="battery_full" size="md" color="primary" />
        </q-tab>
        <!-- <q-tab name="smart-home" title="SmartHome">
          <q-icon name="home" size="md" color="primary" />
        </q-tab> -->
      </q-tabs>
      <!-- Tab Panels -->
      <q-tab-panels v-model="tab" class="col column">
        <!-- Charge Points -->
        <q-tab-panel name="charge-points" class="column">
          <ChargePointInformation />
        </q-tab-panel>
        <!-- Vehicles -->
        <q-tab-panel name="vehicles" class="column">
          <VehicleInformation />
        </q-tab-panel>
        <!-- Batteries -->
        <q-tab-panel v-if="batteryAccessible" name="batteries" class="column">
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
import { computed, ref } from 'vue';
import { useMqttStore } from 'src/stores/mqtt-store';
import ChartCarousel from 'src/components/ChartCarousel.vue';
import ChargePointInformation from 'src/components/ChargePointInformation.vue';
import BatteryInformation from 'src/components/BatteryInformation.vue';
import VehicleInformation from 'src/components/VehicleInformation.vue';
// import SmartHomeInformation from 'src/components/SmartHomeInformation.vue';

defineOptions({
  name: 'IndexPage',
});

const tab = ref<string>('charge-points');
const mqttStore = useMqttStore();

const batteryAccessible = computed(() => {
  return mqttStore.batteryConfigured && mqttStore.batteryIds.length > 0;
});
</script>

<style scoped lang="scss">
.chart-section {
  height: 40vh;
  min-height: 350px;
}

.tab-section,
.tab-section :deep(.q-panel-parent .q-panel) {
  flex-grow: 1;
  display: flex;
  flex-direction: column;
}

.tab-section .q-tab-panel {
  max-width: 100vw;
  flex-grow: 1;
}

@media screen and (max-width: $breakpoint-xs-max) {
  .tab-section .q-tab-panel {
    padding: 0;
  }
}
</style>
