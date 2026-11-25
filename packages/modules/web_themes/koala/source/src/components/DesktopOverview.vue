<template>
  <div class="overview-width-container">
    <section
      class="desktop-overview"
      :class="{
        'overview-with-sidebar': graphCharts.length && visualCharts.length,
        'overview-dark': $q.dark.isActive,
      }"
      :style="{
        '--overview-panel-height': `${localDataStore.historyChartHeight}px`,
      }"
      aria-label="Energieübersicht"
    >
      <DashboardChart
        v-if="valuesChart"
        :chart="valuesChart"
        class="overview-values"
      />
      <div v-if="graphCharts.length" class="overview-graphs">
        <q-tabs
          v-if="graphCharts.length > 1"
          v-model="activeGraph"
          dense
          no-caps
          align="left"
          active-color="primary"
        >
          <q-tab
            v-for="chart in graphCharts"
            :key="chart.name"
            :name="chart.name"
            :label="chart.label"
          />
        </q-tabs>
        <DashboardChart
          v-if="selectedGraph"
          :key="selectedGraph.name"
          :chart="selectedGraph"
        />
      </div>
      <div v-if="visualCharts.length" class="overview-visuals">
        <q-btn
          v-if="visualCharts.length > 1"
          class="visual-switch chart-action-button"
          flat
          dense
          no-caps
          color="primary"
          icon="swap_horiz"
          :label="nextVisual?.label"
          :aria-label="`${nextVisual?.label} anzeigen`"
          @click="activeVisual = nextVisual?.name || activeVisual"
        >
          <q-tooltip>{{ nextVisual?.label }} anzeigen</q-tooltip>
        </q-btn>
        <DashboardChart
          v-if="selectedVisual"
          :key="selectedVisual.name"
          :chart="selectedVisual"
        />
      </div>
      <div v-if="forecastPriceChart" class="overview-combined">
        <DashboardChart :chart="forecastPriceChart" />
      </div>
    </section>
  </div>
</template>

<script setup lang="ts">
import { computed, ref } from 'vue';
import { useQuasar } from 'quasar';
import DashboardChart from './DashboardChart.vue';
import { topCharts, useTopCharts } from './charts/topCharts';
import { useLocalDataStore } from 'src/stores/localData-store';

const localDataStore = useLocalDataStore();
const $q = useQuasar();
const availableCharts = useTopCharts();
// Fixed dashboard order; selection order only determines visibility.
const combinedCharts = computed(() =>
  topCharts.flatMap((chart) =>
    availableCharts.value.filter(
      (available) =>
        available.name === chart.name &&
        localDataStore.desktopSlides.includes(available.name),
    ),
  ),
);
const visualCharts = computed(() =>
  combinedCharts.value.filter((chart) =>
    ['flow_diagram', 'sankey_chart'].includes(chart.name),
  ),
);
const valuesChart = computed(() =>
  combinedCharts.value.find((chart) => chart.name === 'daily_totals'),
);
const graphCharts = computed(() =>
  combinedCharts.value.filter((chart) => chart.name === 'history_chart'),
);
const forecastPriceChart = computed(() =>
  combinedCharts.value.find((chart) => chart.name === 'forecast_price_chart'),
);
const activeGraph = ref('history_chart');
const activeVisual = computed({
  get: () =>
    visualCharts.value.some(
      (chart) => chart.name === localDataStore.dashboardVisual,
    )
      ? localDataStore.dashboardVisual
      : visualCharts.value[0]?.name || '',
  set: (value: string) => {
    localDataStore.dashboardVisual = value;
  },
});
const selectedGraph = computed(
  () =>
    graphCharts.value.find((chart) => chart.name === activeGraph.value) ||
    graphCharts.value[0],
);
const selectedVisual = computed(() =>
  visualCharts.value.find((chart) => chart.name === activeVisual.value),
);
const nextVisual = computed(() => {
  const index = visualCharts.value.findIndex(
    (chart) => chart.name === activeVisual.value,
  );
  return visualCharts.value[(index + 1) % visualCharts.value.length];
});
</script>

<style scoped>
.overview-width-container {
  container-type: inline-size;
  width: 100%;
  min-width: 0;
}
.desktop-overview {
  display: grid;
  grid-template-columns: minmax(0, 1fr);
  gap: var(--dashboard-gap);
  width: 100%;
  min-width: 0;
}
.overview-dark {
  --q-home-stroke: #8c8c8c;
}
.overview-graphs,
.overview-combined,
.overview-visuals {
  display: flex;
  flex-direction: column;
  min-width: 0;
  background: var(--q-card-background);
  border-radius: var(--dashboard-radius);
  padding: var(--dashboard-panel-padding);
  height: var(--overview-panel-height);
  min-height: 0;
}
.overview-graphs :deep(.chart-container) {
  border-radius: var(--dashboard-radius);
  filter: none;
}
.overview-values {
  grid-column: 1 / -1;
}
.overview-combined {
  grid-column: 1 / -1;
}
.overview-visuals {
  position: relative;
}
.visual-switch {
  align-self: flex-end;
  flex: 0 0 auto;
  margin-bottom: 8px;
}
.overview-graphs :deep(.dashboard-chart),
.overview-combined :deep(.dashboard-chart),
.overview-visuals :deep(.dashboard-chart) {
  flex: 1;
  min-height: 0;
  justify-content: center;
}
@container (min-width: 1000px) {
  .overview-with-sidebar {
    grid-template-columns: repeat(2, minmax(0, 1fr));
  }
}
</style>
