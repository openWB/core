<template>
  <div class="chart-container">
    <div class="chart-wrapper">
      <ChartjsSankey
        v-if="hasFlows"
        :key="edgeCount"
        :data="chartData"
        :options="chartOptions"
        :plugins="chartPlugins"
      />
      <div v-else class="sankey-empty text-grey text-center">
        Aktuell kein Energiefluss
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue';
import { useQuasar } from 'quasar';
import { createTypedChart } from 'vue-chartjs';
import { Tooltip, LinearScale } from 'chart.js';
import { SankeyController, Flow } from 'chartjs-chart-sankey';
import type { ChartData, ChartOptions, TooltipItem } from 'chart.js';
import type { SankeyDataPoint } from 'chartjs-chart-sankey';
import { useSankeyData } from './useSankeyData';
import { useSankeyHover } from './useSankeyHover';

// A typed sankey component (like vue-chartjs's built-in Line/Bar) so the
// `data`/`options` props are fixed to 'sankey' instead of the whole ChartType
// union. createTypedChart also registers what we pass: the sankey controller
// and element, plus the LinearScale its defaults require (non-obvious, since a
// sankey shows no axes) and the Tooltip.
const ChartjsSankey = createTypedChart('sankey', [
  SankeyController,
  Flow,
  LinearScale,
  Tooltip,
]);

defineOptions({ name: 'SankeyChart' });

// Accepted for parity with the other carousel charts; not used here.
defineProps<{ showLegend?: boolean }>();

const $q = useQuasar();
const { allocation, colorForNode, labelColor } = useSankeyData();

const hasFlows = computed(() => allocation.value.edges.length > 0);

// Remount the chart whenever the number of flows changes. The sankey plugin
// rebuilds its whole node map on every parse, but Chart.js parses twice when
// data grows — once for the existing elements, then again for the inserted
// ones. The second parse discards the node objects the existing flows point
// at, so those flows color orphans while the chart paints the new nodes, which
// have no color and fall back to black. A fresh chart parses only once.
const edgeCount = computed(() => allocation.value.edges.length);

const { hoverPlugin, focusColors } = useSankeyHover(colorForNode);
const chartPlugins = [hoverPlugin];

const formatWatts = (watts: number): string => {
  if (Math.abs(watts) >= 1000) {
    return `${(watts / 1000).toLocaleString('de-DE', {
      minimumFractionDigits: 1,
      maximumFractionDigits: 1,
    })} kW`;
  }
  return `${Math.round(watts)} W`;
};

const chartData = computed<ChartData<'sankey'>>(() => {
  // Reference the theme so a light/dark toggle rebuilds data and re-resolves
  // the CSS color variables.
  void $q.dark.isActive;

  // Reading the hover state here (rather than in the color callbacks, which
  // Chart.js calls later) is what makes this recompute on every hover change.
  const flowColor = focusColors();

  const { edges, nodes, sources } = allocation.value;
  const labels: Record<string, string> = {};
  const columns: Record<string, number> = {};
  for (const node of nodes) {
    labels[node.id] = node.label;
    columns[node.id] = sources.some((source) => source.id === node.id) ? 0 : 1;
  }

  const textColor = labelColor();

  return {
    datasets: [
      {
        label: 'Energiefluss',
        data: edges.map((edge) => ({ from: edge.from, to: edge.to, flow: edge.flow })),
        labels,
        column: columns,
        colorFrom: (ctx) =>
          flowColor(
            (ctx.raw as SankeyDataPoint | undefined)?.from ?? '',
            ctx.dataIndex,
          ),
        colorTo: (ctx) =>
          flowColor(
            (ctx.raw as SankeyDataPoint | undefined)?.to ?? '',
            ctx.dataIndex,
          ),
        colorMode: 'gradient',
        borderWidth: 0,
        color: textColor,
        nodeLabels: { color: textColor },
        nodeWidth: 16,
        nodePadding: 12,
      },
    ],
  };
});

const chartOptions = computed<ChartOptions<'sankey'>>(() => ({
  responsive: true,
  maintainAspectRatio: false,
  animation: false,
  plugins: {
    tooltip: {
      callbacks: {
        label: (item: TooltipItem<'sankey'>) => {
          const raw = item.raw as SankeyDataPoint;
          const from = allocation.value.nodes.find((node) => node.id === raw.from);
          const to = allocation.value.nodes.find((node) => node.id === raw.to);
          return `${from?.label ?? raw.from} → ${to?.label ?? raw.to}: ${formatWatts(raw.flow)}`;
        },
      },
    },
  },
}));
</script>

<style scoped>
.chart-container {
  width: 100%;
  height: 100%;
  min-height: 100px;
  display: flex;
  flex-direction: column;
}

.chart-wrapper {
  flex: 1;
  min-height: 0;
  min-width: 0;
  position: relative;
}

.chart-wrapper > canvas {
  width: 100% !important;
  height: 100% !important;
}

.sankey-empty {
  height: 100%;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 1rem;
}
</style>
