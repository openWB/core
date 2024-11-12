<template>
  <div class="row justify-center">
    <BatteryOverview />
  </div>
  <q-carousel
    v-model="currentSlide"
    swipeable
    :animated="animated"
    control-color="primary"
    infinite
    padding
    :navigation="groupedBatteries.length > 1"
    :arrows="groupedBatteries && $q.screen.gt.xs && groupedBatteries.length > 1"
    class="full-width full-height q-mt-md"
    transition-next="slide-left"
    transition-prev="slide-right"
    @mousedown.prevent
  >
    <q-carousel-slide
      v-for="(group, index) in groupedBatteries"
      :key="index"
      :name="index"
      class="row no-wrap justify-center carousel-slide"
    >
      <div
        v-for="batteryId in group"
        :key="batteryId"
        class="battery-container"
      >
        <BatteryInformation :battery-id="batteryId" />
      </div>
    </q-carousel-slide>
  </q-carousel>
</template>

<script setup lang="ts">
import { ref, computed, watch, nextTick } from 'vue';
import { useMqttStore } from 'src/stores/mqtt-store';
import { useQuasar } from 'quasar';
import BatteryInformation from './BatteryInformation.vue';
import BatteryOverview from './BatteryOverview.vue';

const mqttStore = useMqttStore();
const $q = useQuasar();
const currentSlide = ref<number>(0);
const animated = ref<boolean>(true);

/**
 * Group the batteries in chunks of 2 for large screens and 1 for small screens.
 */
const groupedBatteries = computed(() => {
  const groupSize = $q.screen.width > 800 ? 2 : 1;
  return mqttStore.batteryIds.reduce((resultArray, item, index) => {
    const chunkIndex = Math.floor(index / groupSize);
    if (!resultArray[chunkIndex]) {
      resultArray[chunkIndex] = [];
    }
    resultArray[chunkIndex].push(item);
    return resultArray;
  }, [] as number[][]);
});

/**
 * Update the current slide when the grouped batteries change.
 * This may happen when the charge points are sorted or filtered or when the screen size changes.
 * We try to keep the same battery in view when the slide changes.
 */
watch(
  () => groupedBatteries.value,
  async (newValue, oldValue) => {
    const findSlide = (batteryId: number) => {
      return newValue.findIndex((group) => group.includes(batteryId));
    };

    if (!oldValue || oldValue.length === 0) {
      currentSlide.value = 0;
      return;
    }

    // Prevent animation when the current slide is modified
    animated.value = false;
    currentSlide.value = Math.max(
      findSlide(oldValue[currentSlide.value][0]),
      0,
    );
    await nextTick();
    animated.value = true;
  },
  { immediate: true },
);
</script>

<style scoped>
.carousel-slide {
  padding: 0;
}
.battery-container {
  padding: 0.25em;
}
</style>




