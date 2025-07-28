<template>
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

const batteryIds = computed(() => {
  let ids = mqttStore.batteryIds;
  if (ids.length > 1) {
    return [-1].concat(ids); // add overview card if more than one battery
  }
  return ids;
});
</script>
