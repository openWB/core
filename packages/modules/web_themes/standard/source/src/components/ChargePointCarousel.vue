<template>
  <div>
    <q-carousel
      v-model="slide"
      swipeable
      animated
      control-color="primary"
      infinite
      :navigation="$q.screen.gt.xs"
      :arrows="$q.screen.gt.xs"
      class="full-height"
      @mousedown.prevent
    >
      <q-carousel-slide
        v-for="(group, index) in groupedChargePoints"
        :key="index"
        :name="index"
        class="row no-wrap justify-center"
      >
        <div v-for="chargePointId in group" :key="chargePointId" class="">
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
const chargePointIds = computed(() => mqttStore.getChargePointIds);

// Returns an array of arrays, where each inner array contains 1 or 2 or 3 chargePointIds
// depending on screen size
const groupedChargePoints = computed(() => {
  let groupSize = 1;
  if ($q.screen.width >= 1100) {
    groupSize = 3;
  } else if ($q.screen.width >= 800) {
    groupSize = 2;
  }
  return chargePointIds.value.reduce((resultArray, item, index) => {
    const chunkIndex = Math.floor(index / groupSize);
    if (!resultArray[chunkIndex]) {
      resultArray[chunkIndex] = [];
    }
    resultArray[chunkIndex].push(item);
    return resultArray;
  }, [] as number[][]);
});

// Set initial slide when data is available
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
  width: 100%;
  max-width: 800px;
  margin: 0 auto;
}

.custom-carousel {
  padding: 0 !important;
}

.custom-carousel-slide {
  padding: 0 !important;
}

.custom-charge-point-container {
  width: 100%;
  padding: 0;
}

/* Target the inner content of q-carousel */
.custom-carousel > .q-carousel__slides {
  padding: 0 !important;
}

/* Target the slide wrapper */
.custom-carousel > .q-carousel__slide {
  padding: 0 !important;
}
</style>
