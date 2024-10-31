<template>
  <q-carousel
    v-model="slide"
    swipeable
    animated
    control-color="primary"
    infinite
    padding
    :navigation="groupedChargePoints.length > 1"
    :arrows="groupedChargePoints && $q.screen.gt.xs"
    class="full-width full-height q-mt-md"
    transition-next="slide-left"
    transition-prev="slide-right"
    @mousedown.prevent
  >
    <q-carousel-slide
      v-for="(group, index) in groupedChargePoints"
      :key="index"
      :name="index"
      class="row no-wrap justify-center carousel-slide"
    >
      <div
        v-for="chargePointId in group"
        :key="chargePointId"
        class="charge-point-container"
      >
        <ChargePoint :charge-point-id="chargePointId" />
      </div>
    </q-carousel-slide>
  </q-carousel>
</template>

<script setup lang="ts">
import { ref, computed, watch } from 'vue';
import { useMqttStore } from 'src/stores/mqtt-store';
import { useQuasar } from 'quasar';
import ChargePoint from './ChargePoint.vue';

const mqttStore = useMqttStore();
const $q = useQuasar();
const slide = ref<number | undefined>(undefined);

const chargePointIds = ref<number[]>([]);
watch(
  () => mqttStore.chargePointIds,
  (newIds) => {
    chargePointIds.value = newIds;
    if (newIds.length > 0 && slide.value === undefined) {
      slide.value = 0;
    }
  },
  { immediate: true }
);

const groupedChargePoints = computed(() => {
  const groupSize = $q.screen.width > 800 ? 2 : 1;
  return chargePointIds.value.reduce((resultArray, item, index) => {
    const chunkIndex = Math.floor(index / groupSize);
    if (!resultArray[chunkIndex]) {
      resultArray[chunkIndex] = [];
    }
    resultArray[chunkIndex].push(item);
    return resultArray;
  }, [] as number[][]);
});
</script>

<style scoped>
.carousel-slide {
  padding: 0;
}
.charge-point-container {
  padding: 0.25em;
}
</style>
