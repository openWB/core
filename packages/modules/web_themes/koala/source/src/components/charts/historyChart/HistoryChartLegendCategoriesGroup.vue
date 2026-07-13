<template>
  <div
    class="items-center"
    :class="wrapToGrid ? 'legend-categories-grid' : 'row justify-center'"
  >
    <HistoryChartLegendCategory
      :label="'Komponenten'"
      :items="categorizedLegendItems.component"
      :toggleDataset="toggleDataset"
      :getItemColor="getItemColor"
      :getItemLineType="getItemLineType"
      menuAnchor="bottom right"
      menuSelf="top right"
    />

    <HistoryChartLegendCategory
      :label="'Ladepunkte'"
      :items="categorizedLegendItems.chargepoint"
      :toggleDataset="toggleDataset"
      :getItemColor="getItemColor"
      :getItemLineType="getItemLineType"
      menuAnchor="bottom middle"
      menuSelf="top middle"
      :menuFormat="wrapToGrid ? undefined : 'q-mx-lg'"
    />

    <HistoryChartLegendCategory
      :label="'Fahrzeuge'"
      :items="categorizedLegendItems.vehicle"
      :toggleDataset="toggleDataset"
      :getItemColor="getItemColor"
      :getItemLineType="getItemLineType"
      menuAnchor="bottom middle"
      menuSelf="top middle"
      :menuFormat="wrapToGrid ? undefined : 'q-mx-lg'"
    />

    <HistoryChartLegendCategory
      v-if="categorizedLegendItems.consumer.length"
      :label="'Verbraucher'"
      :items="categorizedLegendItems.consumer"
      :toggleDataset="toggleDataset"
      :getItemColor="getItemColor"
      :getItemLineType="getItemLineType"
      menuAnchor="bottom left"
      menuSelf="top left"
    />
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue';
import { useQuasar } from 'quasar';
import HistoryChartLegendCategory from './HistoryChartLegendCategory.vue';
import type { LegendItem } from 'chart.js';
import type { Category } from './history-chart-model';

const props = defineProps<{
  categorizedLegendItems: Record<Category, LegendItem[]>;
  toggleDataset: (datasetName: string, datasetIndex: number) => void;
  getItemColor: (dataset: LegendItem) => string;
  getItemLineType: (dataset: LegendItem) => string | undefined;
}>();

const $q = useQuasar();
const wrapToGrid = computed(
  () =>
    props.categorizedLegendItems.consumer.length > 0 && $q.screen.width < 700,
);
</script>

<style scoped>
.legend-categories-grid {
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  justify-items: stretch;
  gap: 4px 8px;
}

.legend-categories-grid :deep(.q-btn) {
  margin: 0;
  width: 100%;
}
</style>
