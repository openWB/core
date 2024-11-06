<template>
  <q-carousel
    v-model="currentSlide"
    swipeable
    :animated="animated"
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
import { ref, computed, watch, nextTick } from 'vue';
import { useMqttStore } from 'src/stores/mqtt-store';
import { useQuasar } from 'quasar';
import ChargePoint from './ChargePoint.vue';

const mqttStore = useMqttStore();
const $q = useQuasar();
const currentSlide = ref<number>(0);
const animated = ref<boolean>(true);

/**
 * Group the charge points in chunks of 2 for large screens and 1 for small screens.
 */
const groupedChargePoints = computed(() => {
  const groupSize = $q.screen.width > 800 ? 2 : 1;
  return mqttStore.chargePointIds.reduce((resultArray, item, index) => {
    const chunkIndex = Math.floor(index / groupSize);
    if (!resultArray[chunkIndex]) {
      resultArray[chunkIndex] = [];
    }
    resultArray[chunkIndex].push(item);
    return resultArray;
  }, [] as number[][]);
});

/**
 * Update the current slide when the grouped charge points change.
 * This may happen when the charge points are sorted or filtered or when the screen size changes.
 * We try to keep the same charge point in view when the slide changes.
 */
watch(
  () => groupedChargePoints.value,
  async (newValue, oldValue) => {
    const findSlide = (chargePointId: number) => {
      return newValue.findIndex((group) => {
        return group.includes(chargePointId);
      });
    };
    if (oldValue === undefined || oldValue.length === 0) {
      currentSlide.value = 0;
      return;
    }
    // Prevent animation when the current slide is modified
    animated.value = false;
    currentSlide.value = Math.max(findSlide(oldValue[currentSlide.value][0]), 0);
    await nextTick();
    animated.value = true;
  },
);
</script>

<style scoped>
.carousel-slide {
  padding: 0;
}
.charge-point-container {
  padding: 0.25em;
}
</style>
