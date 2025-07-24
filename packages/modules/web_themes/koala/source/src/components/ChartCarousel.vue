<template>
  <q-carousel
    v-model="currentSlide"
    v-model:fullscreen="fullscreen"
    swipeable
    control-color="primary"
    padding
    animated
    infinite
    :navigation="chartCarouselItems.length > 1"
    :arrows="chartCarouselItems.length > 1 && $q.screen.gt.xs"
    class="full-width full-height bg-transparent carousel-height"
  >
    <q-carousel-slide
      v-for="chartComponent in chartCarouselItems"
      :key="`${chartComponent.name}-${chartComponent.name === 'HistoryChart' ? renderKey : 0}`"
      :name="chartComponent.name"
    >
      <component :is="chartComponent.component" :show-legend="legendVisible" />
    </q-carousel-slide>

    <template v-slot:control>
      <q-carousel-control position="bottom-right">
        <q-btn
          v-if="currentSlide === 'HistoryChart'"
          size="sm"
          class="q-mr-sm legend-button-text"
          label="Legende ein/aus"
          @click="toggleLegend"
        />
        <q-btn
          push
          round
          dense
          text-color="primary"
          :icon="fullscreen ? 'fullscreen_exit' : 'fullscreen'"
          @click="fullscreen = !fullscreen"
        />
      </q-carousel-control>
    </template>
  </q-carousel>
</template>

<script setup lang="ts">
import { ref, computed, watch } from 'vue';
import { useQuasar } from 'quasar';
import EnergyFlowChart from './charts/energyFlowChart/EnergyFlowChart.vue';
import HistoryChart from './charts/historyChart/HistoryChart.vue';
import { useLocalDataStore } from 'src/stores/localData-store';

defineOptions({
  name: 'ChartCarousel',
});
const $q = useQuasar();
const localDataStore = useLocalDataStore();
const renderKey = ref(0);
const toggleLegend = () => {
  localDataStore.toggleLegendVisibility();
};
const legendVisible = computed(() => localDataStore.legendVisible);
const fullscreen = ref(false);
const chartCarouselItems = [
  {
    name: 'EnergyFlowChart',
    component: EnergyFlowChart,
  },
  {
    name: 'HistoryChart',
    component: HistoryChart,
  },
];
const currentSlide = ref<string>(chartCarouselItems[0].name);

watch(
  () => fullscreen.value,
  (isFullscreen, wasFullscreen) => {
    // Only trigger when exiting fullscreen and current slide is HistoryChart
    if (
      !isFullscreen &&
      wasFullscreen &&
      currentSlide.value === 'HistoryChart'
    ) {
      // Force the chart to be recreated by changing its key
      renderKey.value++;
    }
  },
);
</script>

<style scoped>
.carousel-height {
  min-height: fit-content;
}

.legend-button-text {
  color: var(--q-carousel-control);
}
</style>
