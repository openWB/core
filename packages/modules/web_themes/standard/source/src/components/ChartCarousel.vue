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
    class="full-width bg-transparent"
  >
    <q-carousel-slide
      v-for="(chartComponent, index) in chartCarouselItems"
      :key="index"
      :name="chartComponent.name"
      class="col items-center justify-center"
    >
      <component :is="chartComponent" />
    </q-carousel-slide>

    <template v-slot:control>
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
import { ref } from 'vue';
import { useQuasar } from 'quasar';

import EnergyFlowChart from './charts/EnergyFlowChart.vue';
import HistoryChart from './charts/HistoryChart.vue';

defineOptions({
  name: 'ChartCarousel',
});

const $q = useQuasar();
const fullscreen = ref(false);
const chartCarouselItems = [EnergyFlowChart, HistoryChart];
const currentSlide = ref<string>(EnergyFlowChart.__name ?? '');
</script>
