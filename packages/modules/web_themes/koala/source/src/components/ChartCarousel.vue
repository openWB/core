<template>
  <q-carousel
    v-if="chartCarouselItems.length > 0 && currentSlide"
    :key="carouselKey"
    v-model="currentSlide"
    v-model:fullscreen="fullscreen"
    swipeable
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
      <component
        :is="chartComponent.component"
        v-bind="
          chartComponent.name === 'forecast_price_chart'
            ? { dashboard: !!props.includeDashboard }
            : {}
        "
        :show-legend="localDataStore.isLegendVisible(chartComponent.name)"
      />
    </q-carousel-slide>

    <template v-slot:control>
      <q-carousel-control position="bottom-left">
        <q-btn
          v-if="currentSlide === 'history_chart'"
          size="sm"
          push
          class="q-mr-sm legend-button-text"
          label="Legende"
          :aria-pressed="
            currentSlide ? localDataStore.isLegendVisible(currentSlide) : false
          "
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
import { useLocalDataStore } from 'src/stores/localData-store';
import { useTopCharts } from './charts/topCharts';

const props = defineProps<{
  excludedSlides?: string[];
  includeDashboard?: boolean;
}>();
const availableCharts = useTopCharts();

defineOptions({
  name: 'ChartCarousel',
});
const $q = useQuasar();
const localDataStore = useLocalDataStore();
const renderKey = ref(0);
const toggleLegend = () => {
  if (currentSlide.value)
    localDataStore.toggleLegendVisibility(currentSlide.value);
};
const fullscreen = ref(false);

const carouselKey = computed(() =>
  chartCarouselItems.value.map((item) => item.name).join('-'),
);

const currentSlide = ref<string | null>(null);

const chartCarouselItems = computed(() =>
  availableCharts.value.filter(
    (chart) => !props.excludedSlides?.includes(chart.name),
  ),
);

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
    if (
      items.length > 0 &&
      !items.some((item) => item.name === currentSlide.value)
    ) {
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

@media (max-width: 599px) {
  /* Keep all six slide indicators clear of the existing corner controls. */
  :deep(.q-carousel__navigation--bottom) {
    left: 96px;
    right: 54px;
  }
  :deep(.q-carousel__navigation .q-btn) {
    margin: 0;
    padding: 0;
    width: 24px;
    min-width: 24px;
    min-height: 24px;
  }
}
</style>
