<template>
  <section
    class="dashboard-chart"
    :class="`dashboard-${chart.name}`"
    :aria-label="chart.label"
    :data-chart="chart.name"
  >
    <div class="dashboard-chart-body">
      <component
        :is="chart.component"
        v-bind="chart.name !== 'daily_totals' ? { dashboard: true } : {}"
        :show-legend="localDataStore.isLegendVisible(chart.name)"
      />
    </div>
    <div
      v-if="chart.name === 'history_chart'"
      class="dashboard-chart-controls row justify-end"
    >
      <q-btn
        flat
        dense
        no-caps
        class="chart-action-button"
        color="primary"
        label="Legende"
        :aria-pressed="localDataStore.isLegendVisible(chart.name)"
        @click="localDataStore.toggleLegendVisibility(chart.name)"
      />
    </div>
  </section>
</template>

<script setup lang="ts">
import { topCharts } from './charts/topCharts';
import { useLocalDataStore } from 'src/stores/localData-store';

defineProps<{ chart: (typeof topCharts)[number] }>();
const localDataStore = useLocalDataStore();
</script>

<style scoped>
.dashboard-chart {
  display: flex;
  flex-direction: column;
  min-width: 0;
  min-height: 0;
}
.dashboard-chart-body {
  min-width: 0;
  min-height: 0;
}
.dashboard-chart:not(.dashboard-daily_totals) .dashboard-chart-body {
  position: relative;
  flex: 1;
  width: 100%;
}
.dashboard-chart-body :deep(.chart-container),
.dashboard-chart-body :deep(.svg-container) {
  position: absolute;
  inset: 0;
  min-height: 0;
}
.dashboard-chart-controls {
  flex: 0 0 auto;
}
.dashboard-chart-body :deep(.legend-wrapper) {
  max-height: 45%;
  overflow-y: auto;
  flex-shrink: 1;
}
</style>
