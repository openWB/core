// ChargePointCarousel.vue
<template>
  <q-carousel
    v-model="slide"
    swipeable
    animated
    navigation
    arrows
    control-color="primary"
    infinite
    class="full-height"
    @mousedown.prevent
  >
    <q-carousel-slide
      v-for="chargePointId in chargePointIds"
      :key="chargePointId"
      :name="chargePointId"
      class="column align-center"
    >
      <ChargePoint :charge-point-id="chargePointId" />
    </q-carousel-slide>
  </q-carousel>
</template>

<script setup lang="ts">
import { ref, computed, watch, onMounted } from 'vue';
import { useMqttStore } from 'src/stores/mqtt-store';
import ChargePoint from './ChargePoint.vue';

const mqttStore = useMqttStore();
const slide = ref<string | undefined>(undefined);

const chargePointIds = computed(() => mqttStore.getChargePointIds);

// Set initial slide when data is available
watch(
  chargePointIds,
  (newValue) => {
    if (newValue.length > 0 && !slide.value) {
      slide.value = newValue[0];
    }
  },
  { immediate: true },
);

onMounted(() => {
  mqttStore.subscribe(['openWB/chargepoint/+/config']);
});
</script>
