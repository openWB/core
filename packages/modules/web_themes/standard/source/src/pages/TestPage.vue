<template>
  <q-page class="column">
    <!-- Top Carousel -->
    <div class="row justify-center">
      <ChartCarousel />
    </div>

    <!-- Navigation Tabs -->
    <q-tabs v-model="tab" dense class="q-tabs__content--align-justify">
      <q-tab name="charge-points" title="Ladepunkte">
        <q-icon name="ev_station" size="md" color="primary" />
      </q-tab>
      <q-tab name="batteries" title="Speicher">
        <q-icon name="battery_full" size="md" color="warning" />
      </q-tab>
      <q-tab name="smartHome" title="SmartHome">
        <q-icon name="home" size="md" color="accent" />
      </q-tab>
    </q-tabs>

    <!-- Tab Panels -->
    <q-tab-panels v-model="tab" animated class="col">
      <q-tab-panel name="charge-points" class="q-pa-none column">
        <ChargePointCarousel />
      </q-tab-panel>
      <q-tab-panel name="batteries" class="">
        <BatteryCarousel />
      </q-tab-panel>
      <q-tab-panel name="smartHome" class="">
        <SmartHomeInformation />
      </q-tab-panel>
    </q-tab-panels>
  </q-page>
</template>

<script setup lang="ts">
import { ref } from 'vue';
import ChartCarousel from 'src/components/ChartCarousel.vue';
import ChargePointCarousel from 'src/components/ChargePointCarousel.vue';
import SmartHomeInformation from 'src/components/SmartHomeInformation.vue';
import BatteryCarousel from 'src/components/BatteryCarousel.vue';

defineOptions({
  name: 'IndexPage',
});

const tab = ref<string>('charge-points');
</script>
