<template>
  <q-page class="column">
    <!-- Top Carousel -->
    <div class="row justify-center full-width chart-section">
      <ChartCarousel />
    </div>

    <!-- Navigation Tabs -->
    <q-tabs v-model="tab" dense class="q-tabs__content--align-justify">
      <q-tab name="charge-points" title="Ladepunkte">
        <q-icon name="ev_station" size="md" color="primary" />
      </q-tab>
      <q-tab name="batteries" title="Speicher">
        <q-icon name="battery_full" size="md" color="primary" />
      </q-tab>
      <q-tab name="smartHome" title="SmartHome">
        <q-icon name="home" size="md" color="primary" />
      </q-tab>
    </q-tabs>
    <!-- Tab Panels -->
    <q-tab-panels v-model="tab" class="col">
      <q-tab-panel name="charge-points" class="q-pa-none column">
        <BaseCarousel :items="chargePointIds">
          <template #item="{ item }">
            <ChargePoint :charge-point-id="item" />
          </template>
        </BaseCarousel>
      </q-tab-panel>
      <q-tab-panel name="batteries" class="">
        <div v-if="showBatteryOverview" class="row justify-center">
          <BatteryOverview />
        </div>
        <BaseCarousel :items="batteryIds">
          <template #item="{ item }">
            <BatteryInformation :battery-id="item" />
          </template>
        </BaseCarousel>
      </q-tab-panel>
      <q-tab-panel name="smartHome" class="">
        <SmartHomeInformation />
      </q-tab-panel>
    </q-tab-panels>
  </q-page>
</template>

<script setup lang="ts">
import { ref, computed } from 'vue';
import { useMqttStore } from 'src/stores/mqtt-store';
import ChartCarousel from 'src/components/ChartCarousel.vue';
import BaseCarousel from 'src/components/BaseCarousel.vue';
import ChargePoint from 'src/components/ChargePoint.vue';
import BatteryInformation from 'src/components/BatteryInformation.vue';
import BatteryOverview from 'src/components/BatteryOverview.vue';
import SmartHomeInformation from 'src/components/SmartHomeInformation.vue';

defineOptions({
  name: 'IndexPage',
});

const tab = ref<string>('charge-points');

const showBatteryOverview = computed(() => {
  return mqttStore.batteryIds.length > 1;
});

const mqttStore = useMqttStore();
const chargePointIds = computed(() => mqttStore.chargePointIds);
const batteryIds = computed(() => mqttStore.batteryIds);
</script>

<style scoped>
.chart-section {
  height: 40vh;
}
</style>
