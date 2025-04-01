<template>
  <BaseCarousel :items="chargePointIds">
    <template #item="{ item }">
      <ChargePointCard :charge-point-id="item" />
    </template>
  </BaseCarousel>
</template>

<script setup lang="ts">
import { computed } from 'vue';
import { useMqttStore } from 'src/stores/mqtt-store';

import BaseCarousel from 'src/components/BaseCarousel.vue';
import ChargePointCard from 'src/components/ChargePointCard.vue';

const mqttStore = useMqttStore();

const chargePointIds = computed(() => mqttStore.chargePointIds);
</script>
