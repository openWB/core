<template>
  <div class="chart-container">
    <div class="chart-wrapper">
      <ChartjsSankey
        v-if="hasFlows"
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
import { computed, ref } from 'vue';
import { useQuasar } from 'quasar';
import { createTypedChart } from 'vue-chartjs';
import { Tooltip, LinearScale } from 'chart.js';
import { SankeyController, Flow } from 'chartjs-chart-sankey';
import type { ChartData, ChartOptions, Plugin, TooltipItem } from 'chart.js';
import type { SankeyDataPoint } from 'chartjs-chart-sankey';
import { useSankeyData } from './useSankeyData';

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

// Index of the flow currently under the cursor (null = none). Used to fade all
// other flows so the hovered one stands out, like other Sankey products.
const hoveredIndex = ref<number | null>(null);

// Non-hovered flows are pushed toward grey so the hovered one keeps its color.
// The plugin re-applies its own alpha to flow gradients, so fading by alpha
// alone changes only the nodes, not the flows — we must change the RGB.
const FADE_TOWARD = 150; // mid grey (neutral in light and dark)
const FADE_AMOUNT = 0.65; // 0 = untouched, 1 = fully grey

// Parse a hex or rgb/rgba colour string to its RGB channels.
const toRgb = (color: string): { r: number; g: number; b: number } | null => {
  if (color.startsWith('#')) {
    let hex = color.slice(1);
    if (hex.length === 3) {
      hex = hex
        .split('')
        .map((char) => char + char)
        .join('');
    }
    const value = parseInt(hex, 16);
    return { r: (value >> 16) & 255, g: (value >> 8) & 255, b: value & 255 };
  }
  const match = color.match(/rgba?\(([^)]+)\)/);
  if (match) {
    const [r, g, b] = match[1].split(',').map((part) => parseInt(part.trim(), 10));
    return { r, g, b };
  }
  return null;
};

// Faded version of a colour for non-hovered flows: mixed toward grey.
const fade = (color: string): string => {
  const rgb = toRgb(color);
  if (rgb === null) {
    return color;
  }
  const mix = (channel: number) =>
    Math.round(channel * (1 - FADE_AMOUNT) + FADE_TOWARD * FADE_AMOUNT);
  return `rgb(${mix(rgb.r)}, ${mix(rgb.g)}, ${mix(rgb.b)})`;
};

// The color for one end of a flow, faded when another flow is hovered.
// `hovered` is passed in (not read from the ref) so that chartData, which
// captures it, re-runs and yields a fresh dataset whenever the hover changes —
// that is what forces Chart.js to re-resolve the flow colors.
const flowColor = (
  nodeId: string,
  dataIndex: number,
  hovered: number | null,
): string => {
  const base = colorForNode(nodeId);
  return hovered !== null && dataIndex !== hovered ? fade(base) : base;
};

// Hover is tracked from a plugin rather than the `onHover` option
const hoverFocus: Plugin<'sankey'> = {
  id: 'sankeyHoverFocus',
  afterEvent(chart, args) {
    // Ignore the post-update replay: it re-reports a stale in-area position and
    // would resurrect a highlight we just cleared.
    if (args.replay) {
      return;
    }
    const left = !args.inChartArea || args.event.type === 'mouseout';
    hoveredIndex.value = left
      ? null
      : (chart.getActiveElements()[0]?.index ?? null);
  },
};

const chartPlugins = [hoverFocus];

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

  // Capturing the hovered flow here makes this recompute (and emit a fresh
  // dataset) on every hover change, which is what forces Chart.js to re-resolve
  // the flow colors
  const hovered = hoveredIndex.value;

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
            hovered,
          ),
        colorTo: (ctx) =>
          flowColor(
            (ctx.raw as SankeyDataPoint | undefined)?.to ?? '',
            ctx.dataIndex,
            hovered,
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
