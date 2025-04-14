<template>
  <BaseCarousel :items="vehicleIds">
    <template #item="{ item }">
      <VehicleCard :vehicle-id="item" />
    </template>
  </BaseCarousel>
</template>

<script setup lang="ts">
import { computed } from 'vue';
import { useMqttStore } from 'src/stores/mqtt-store';

import BaseCarousel from 'src/components/BaseCarousel.vue';
import VehicleCard from 'src/components/VehicleCard.vue';

const mqttStore = useMqttStore();

const vehicles = computed(() => mqttStore.vehicleList);

const vehicleIds = computed(() => vehicles.value.map((vehicle) => vehicle.id));
</script>
