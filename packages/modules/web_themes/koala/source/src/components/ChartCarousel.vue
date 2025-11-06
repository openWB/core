<template>
  <q-carousel
    v-if="chartCarouselItems.length > 0 && currentSlide"
    :key="carouselKey"
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
      :key="`${chartComponent.name}-${chartComponent.name === 'history_chart' ? renderKey : 0}`"
      :name="chartComponent.name"
    >
      <component :is="chartComponent.component" :show-legend="legendVisible" />
    </q-carousel-slide>

    <template v-slot:control>
      <q-carousel-control position="bottom-left">
        <q-btn
          v-if="currentSlide === 'history_chart'"
          size="sm"
          class="q-mr-sm legend-button-text"
          label="Legend ein/aus"
          @click="toggleLegend"
        />
      </q-carousel-control>
      <q-carousel-control position="bottom-right">
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
import DailyTotals from './DailyTotals.vue';
import { useLocalDataStore } from 'src/stores/localData-store';
import { useMqttStore } from 'src/stores/mqtt-store';

const mqttStore = useMqttStore();

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

const carouselKey = computed(() =>
  chartCarouselItems.value.map((item) => item.name).join('-'),
);

const currentSlide = ref<string | null>(null);

const componentMap = {
  flow_diagram: EnergyFlowChart,
  history_chart: HistoryChart,
  daily_totals: DailyTotals,
};

const chartCarouselItems = computed(() => {
  const slideOrder = mqttStore.themeConfiguration?.top_carousel_slide_order;
  if (!slideOrder || slideOrder.length === 0) {
    return [
      {
        name: 'flow_diagram',
        component: EnergyFlowChart,
      },
      {
        name: 'history_chart',
        component: HistoryChart,
      },
      {
        name: 'daily_totals',
        component: DailyTotals,
      },
    ];
  }
  return slideOrder
    .map((name) => ({
      name,
      component: componentMap[name],
    }))
    .filter((item) => !!item.component);
});

watch(
  () => fullscreen.value,
  (isFullscreen, wasFullscreen) => {
    // Only trigger when exiting fullscreen and current slide is HistoryChart
    if (
      !isFullscreen &&
      wasFullscreen &&
      currentSlide.value === 'history_chart'
    ) {
      // Force the chart to be recreated by changing its key
      renderKey.value++;
    }
  },
);

watch(
  chartCarouselItems,
  (items) => {
    if (items.length > 0) {
      currentSlide.value = items[0].name;
    }
  },
  { immediate: true },
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
