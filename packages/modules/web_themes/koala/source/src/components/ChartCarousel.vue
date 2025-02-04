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
      v-for="(chartComponent, index) in chartCarouselItems"
      :key="index"
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
          label="Legend ein/aus"
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
import { ref } from 'vue';
import { useQuasar } from 'quasar';
import EnergyFlowChart from './charts/energyFlowChart/EnergyFlowChart.vue';
import HistoryChart from './charts/historyChart/HistoryChart.vue';

defineOptions({
  name: 'ChartCarousel',
});
const $q = useQuasar();

const legendVisible = ref(!$q.platform.is.mobile);

const toggleLegend = () => {
  legendVisible.value = !legendVisible.value;
};

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
</script>

<style scoped>
.carousel-height {
  min-height: fit-content;
}

.legend-button-text {
  color: var(--q-carousel-control);
}
</style>
