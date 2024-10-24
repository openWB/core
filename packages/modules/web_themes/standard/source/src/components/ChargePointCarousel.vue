<template>
  <div class="carousel-container">
    <q-carousel
      v-model="slide"
      swipeable
      animated
      control-color="primary"
      infinite
      padding
      :navigation="$q.screen.gt.xs"
      :arrows="$q.screen.gt.xs"
      class="full-height q-mt-md"
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
  </div>
</template>

<script setup lang="ts">
import { ref, computed, watch, onMounted } from 'vue';
import { useMqttStore } from 'src/stores/mqtt-store';
import { useQuasar } from 'quasar';
import ChargePoint from './ChargePoint.vue';

const mqttStore = useMqttStore();
const $q = useQuasar();
const slide = ref<number | undefined>(undefined);

const chargePointIds = computed(() => mqttStore.chargePointIds);
const groupedChargePoints = computed(() => {
  const groupSize = $q.screen.width >= 800 ? 2 : 1;
  return chargePointIds.value.reduce((resultArray, item, index) => {
    const chunkIndex = Math.floor(index / groupSize);
    if (!resultArray[chunkIndex]) {
      resultArray[chunkIndex] = [];
    }
    resultArray[chunkIndex].push(item);
    return resultArray;
  }, [] as number[][]);
});
watch(
  chargePointIds,
  (newValue) => {
    if (newValue.length > 0 && slide.value === undefined) {
      slide.value = 0;
    }
  },
  { immediate: true },
);

onMounted(() => {
  mqttStore.subscribe(['openWB/chargepoint/+/config']);
});
</script>

<style scoped>
.carousel-container {
  max-width: 800px;
  margin: 0 auto;
}
.carousel-slide {
  padding: 0;
}
.charge-point-container {
  width: 100%;
  padding: 8px;
  box-sizing: border-box;
  overflow: hidden;
}
@media (max-width: 600px) {
  .charge-point-container {
    padding: 4px;
  }
}
</style>
