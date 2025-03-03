<template>
  <div v-if="showBatteryOverview" class="row justify-center">
    <BatteryCard :battery-id="undefined" />
  </div>
  <BaseCarousel :items="batteryIds">
    <template #item="{ item }">
      <BatteryCard :battery-id="item" />
    </template>
  </BaseCarousel>
</template>

<script setup lang="ts">
import { computed } from 'vue';
import { useMqttStore } from 'src/stores/mqtt-store';

import BaseCarousel from 'src/components/BaseCarousel.vue';
import BatteryCard from 'src/components/BatteryCard.vue';

const mqttStore = useMqttStore();

const batteryIds = computed(() => mqttStore.batteryIds);

const showBatteryOverview = computed(() => {
  return mqttStore.batteryIds.length > 1;
});
</script>
