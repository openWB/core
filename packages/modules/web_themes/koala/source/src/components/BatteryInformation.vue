<template>
  <div v-if="showBatteryOverview" class="row justify-center">
    <BatteryCard :battery-id="undefined"/>
  </div>
  <BaseCarousel :items="batteryIds" :card-width="cardWidth">
    <template #item="{ item }">
      <BatteryCard :battery-id="item" @card-width="cardWidth = $event"/>
    </template>
  </BaseCarousel>
</template>

<script setup lang="ts">
import { computed, ref } from 'vue';
import { useMqttStore } from 'src/stores/mqtt-store';

import BaseCarousel from 'src/components/BaseCarousel.vue';
import BatteryCard from 'src/components/BatteryCard.vue';

const cardWidth = ref<number | undefined>(undefined);

const mqttStore = useMqttStore();

const batteryIds = computed(() => mqttStore.batteryIds);

const showBatteryOverview = computed(() => {
  return mqttStore.batteryIds.length > 1;
});
</script>
