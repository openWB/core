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
      menuFormat="q-mx-lg"
    />

    <HistoryChartLegendCategory
      :label="'Fahrzeuge'"
      :items="categorizedLegendItems.vehicle"
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
import type { Category } from './history-chart-model';

defineProps<{
  categorizedLegendItems: Record<Category, LegendItem[]>;
  toggleDataset: (datasetName: string, datasetIndex: number) => void;
  getItemColor: (dataset: LegendItem) => string;
  getItemLineType: (dataset: LegendItem) => string | undefined;
}>();
</script>
