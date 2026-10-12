<template>
  <div class="row justify-center items-center">
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
    />

    <HistoryChartLegendCategory
      :label="'Fahrzeuge'"
      :items="categorizedLegendItems.vehicle"
      :toggleDataset="toggleDataset"
      :getItemColor="getItemColor"
      :getItemLineType="getItemLineType"
      menuAnchor="bottom middle"
      menuSelf="top middle"
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
import HistoryChartLegendCategory from './HistoryChartLegendCategory.vue';
import type { LegendItem } from 'chart.js';
import type { Category, LegendItemWithCategory } from './history-chart-model';

defineProps<{
  categorizedLegendItems: Record<Category, LegendItemWithCategory[]>;
  toggleDataset: (datasetKey: string | undefined, datasetIndex: number) => void;
  getItemColor: (dataset: LegendItem) => string;
  getItemLineType: (dataset: LegendItem) => string | undefined;
}>();
</script>

<style scoped>
:deep(.q-btn):not(:first-child) {
  margin-left: 4px;
}
:deep(.q-btn) .q-btn-dropdown__arrow {
  margin-left: 0;
}
</style>
