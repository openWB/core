<template>
  <div ref="container" class="chart-container">
    <div class="chart-wrapper">
      <ChartjsSankey
        v-if="hasFlows && fontsReady"
        :key="edgeCount"
        :data="chartData"
        :options="chartOptions"
        :plugins="chartPlugins"
      />
      <div v-else-if="!hasFlows" class="sankey-empty text-grey text-center">
        Aktuell kein Energiefluss
      </div>
    </div>
    <div
      v-if="hasFlows && (fallbackNodes.length || fallbackFlows.length)"
      class="sankey-details legend-wrapper"
      tabindex="0"
      aria-label="Beschriftungen und weitere Energieflüsse"
    >
      <div v-if="fallbackNodes.length" class="sankey-node-legend">
        <div v-for="item in fallbackNodes" :key="item.id" class="legend-item">
          <span
            class="legend-swatch"
            :style="{ backgroundColor: item.color }"
          />
          <span>{{ item.label }}</span>
        </div>
      </div>
      <ul
        v-if="fallbackFlows.length"
        class="sankey-flow-list"
        aria-label="Weitere Leistungswerte"
      >
        <li v-for="item in fallbackFlows" :key="item.id">
          <span class="flow-route">{{ item.from }} → {{ item.to }}</span>
          <strong>{{ item.power }}</strong>
        </li>
      </ul>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed, onMounted, onBeforeUnmount, ref, shallowRef } from 'vue';
import { useQuasar } from 'quasar';
import { createTypedChart } from 'vue-chartjs';
import { LinearScale, Tooltip } from 'chart.js';
import { SankeyController, Flow } from 'chartjs-chart-sankey';
import type { ChartData, ChartOptions } from 'chart.js';
import type { SankeyDataPoint } from 'chartjs-chart-sankey';
import { useSankeyData } from './useSankeyData';
import { useSankeyHover } from './useSankeyHover';
import { createFlowLabels } from './sankey-flow-labels';
import type { SankeyLabelLayout } from './sankey-flow-labels';
import { NODE_HOUSE, NODE_HOUSE_REST } from './energy-allocation';

// A typed sankey component (like vue-chartjs's built-in Line/Bar) so the
// `data`/`options` props are fixed to 'sankey' instead of the whole ChartType
// union. createTypedChart also registers what we pass: the sankey controller
// and element, plus the LinearScale its defaults require (a sankey has no axes).
const ChartjsSankey = createTypedChart('sankey', [
  SankeyController,
  Flow,
  LinearScale,
  Tooltip,
]);

defineOptions({ name: 'SankeyChart' });

const props = defineProps<{ showLegend?: boolean; dashboard?: boolean }>();

const $q = useQuasar();
const { allocation, colorForNode, labelColor } = useSankeyData();
const container = ref<HTMLElement>();
const fontsReady = ref(false);
const containerSize = shallowRef({ width: 0, height: 0 });
let observer: ResizeObserver | undefined;
onMounted(() => {
  observer = new ResizeObserver(([entry]) => {
    containerSize.value = {
      width: entry.contentRect.width,
      height: entry.contentRect.height,
    };
  });
  if (container.value) observer.observe(container.value);
  // Canvas text is not repainted automatically after a webfont loads.
  // Load the medium weight before the first measurement and collision pass.
  const family = container.value
    ? getComputedStyle(container.value).fontFamily
    : 'sans-serif';
  const ready = () => {
    fontsReady.value = true;
  };
  void document.fonts.load(`500 16px ${family}`).then(ready, ready);
});
onBeforeUnmount(() => observer?.disconnect());
// Use the card's real dimensions, including the space beside an open drawer.
const compact = computed(
  () =>
    containerSize.value.width <
      (allocation.value.houseParts.length ? 640 : 480) ||
    containerSize.value.height < 240,
);
const labelLayout = shallowRef<SankeyLabelLayout>({
  missingNodes: [],
  missingFlows: [],
});

const hasFlows = computed(() => allocation.value.edges.length > 0);

// Remount the chart whenever the number of flows changes. The sankey plugin
// rebuilds its whole node map on every parse, but Chart.js parses twice when
// data grows — once for the existing elements, then again for the inserted
// ones. The second parse discards the node objects the existing flows point
// at, so those flows color orphans while the chart paints the new nodes, which
// have no color and fall back to black. A fresh chart parses only once.
const edgeCount = computed(() => allocation.value.edges.length);

const formatWatts = (watts: number): string => {
  if (Math.abs(watts) >= 1000) {
    return `${(watts / 1000).toLocaleString(undefined, {
      minimumFractionDigits: 1,
      maximumFractionDigits: 1,
    })} kW`;
  }
  return `${Math.round(watts)} W`;
};

const { hoverPlugin, focusColors } = useSankeyHover(colorForNode);

const flowLabels = createFlowLabels({
  format: formatWatts,
  color: labelColor,
  showNodeNames: () => !compact.value,
  onLayout: (layout) => {
    // Avoid Vue updates on every hover/repaint when the fallback is unchanged.
    if (JSON.stringify(layout) !== JSON.stringify(labelLayout.value))
      labelLayout.value = layout;
  },
});
const chartPlugins = [hoverPlugin, flowLabels.plugin];

// Assign a per-column priority from node power.
// Sources descending (largest on top).
// Sinks ascending (largest on the bottom). When the household splits into a
// third column it goes on top instead, level with its parts, so the split
// does not have to cross the other sinks.
// House parts descending, the remainder last.
const nodePriority = computed(() => {
  const { sources, sinks, houseParts } = allocation.value;
  const houseSplit = houseParts.length > 0;
  const priority: Record<string, number> = {};
  [...sources]
    .sort((a, b) => b.power - a.power)
    .forEach((node, index) => {
      priority[node.id] = index;
    });
  [...sinks]
    .sort((a, b) => a.power - b.power)
    .forEach((node, index) => {
      priority[node.id] = houseSplit && node.id === NODE_HOUSE ? -1 : index;
    });
  [...houseParts]
    .sort((a, b) =>
      a.id === NODE_HOUSE_REST
        ? 1
        : b.id === NODE_HOUSE_REST
          ? -1
          : b.power - a.power,
    )
    .forEach((node, index) => {
      priority[node.id] = index;
    });
  return priority;
});

const chartData = computed<ChartData<'sankey'>>(() => {
  // Reference the theme so a light/dark toggle rebuilds data and re-resolves
  // the CSS color variables.
  void $q.dark.isActive;
  // Reading the hover state here (rather than in the color callbacks, which
  // Chart.js calls later) is what makes this recompute on every hover change.
  const flowColor = focusColors();
  const { edges, nodes } = allocation.value;
  const labels: Record<string, string> = {};
  const columns: Record<string, number> = {};
  for (const node of nodes) {
    labels[node.id] = node.label;
    columns[node.id] = node.column;
  }

  const textColor = labelColor();

  return {
    datasets: [
      {
        label: 'Energiefluss',
        data: edges.map((edge) => ({
          from: edge.from,
          to: edge.to,
          flow: edge.flow,
        })),
        labels,
        column: columns,
        priority: nodePriority.value,
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
        // Names and values share the custom collision pass below.
        nodeLabels: { display: false },
        nodeWidth: props.dashboard ? 8 : 16,
        nodePadding: compact.value ? 16 : 24,
        alpha: props.dashboard ? 0.3 : 0.5,
      },
    ],
  };
});

const legendItems = computed(() => {
  void $q.dark.isActive;
  const priority = nodePriority.value;
  return [...allocation.value.nodes]
    .sort(
      (a, b) =>
        a.column - b.column || (priority[a.id] ?? 0) - (priority[b.id] ?? 0),
    )
    .map((node) => ({
      id: node.id,
      label: node.label,
      color: colorForNode(node.id),
    }));
});

const fallbackNodes = computed(() =>
  legendItems.value.filter(
    (item) => compact.value || labelLayout.value.missingNodes.includes(item.id),
  ),
);
const fallbackFlows = computed(() =>
  labelLayout.value.missingFlows.flatMap((index) => {
    const edge = allocation.value.edges[index];
    if (!edge) return [];
    const name = (id: string) =>
      allocation.value.nodes.find((node) => node.id === id)?.label ?? id;
    return [
      {
        id: `${edge.from}-${edge.to}`,
        from: name(edge.from),
        to: name(edge.to),
        power: formatWatts(edge.flow),
      },
    ];
  }),
);

const chartOptions = computed<ChartOptions<'sankey'>>(() => ({
  responsive: true,
  maintainAspectRatio: false,
  animation: false,
  font: {
    family: container.value
      ? getComputedStyle(container.value).fontFamily
      : 'sans-serif',
    size: 16,
    lineHeight: 1.2,
  },
  layout: { padding: 8 },
  plugins: {
    tooltip: {
      displayColors: false,
      // Only flows whose value is not already drawn on the band.
      filter: (item) => !flowLabels.labelled.has(item.dataIndex),
      callbacks: {
        title: () => '',
        label: (item) => {
          const edge = item.raw as SankeyDataPoint;
          const name = (id: string) =>
            allocation.value.nodes.find((node) => node.id === id)?.label ?? id;
          return `${name(edge.from)} → ${name(edge.to)}: ${formatWatts(edge.flow)}`;
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

.legend-wrapper {
  flex: 0 0 auto;
  max-height: 45%;
  overflow-y: auto;
  min-height: 0;
  margin-top: 6px;
  font-size: 16px;
  line-height: 1.4;
  scrollbar-gutter: stable;
}

.sankey-node-legend {
  display: flex;
  flex-wrap: wrap;
  justify-content: center;
  gap: 4px 14px;
}

.legend-item {
  display: flex;
  align-items: center;
  min-width: 0;
  max-width: 100%;
  overflow-wrap: anywhere;
}

.sankey-flow-list {
  list-style: none;
  padding: 0;
  margin: 6px 0 0;
  display: grid;
  gap: 4px;
}

.sankey-flow-list li {
  display: flex;
  align-items: baseline;
  justify-content: space-between;
  gap: 12px;
}

.flow-route {
  overflow-wrap: anywhere;
  min-width: 0;
}

.sankey-flow-list strong {
  flex-shrink: 0;
  font-weight: 500;
  font-variant-numeric: tabular-nums;
}

.legend-swatch {
  width: 10px;
  height: 10px;
  border-radius: 2px;
  margin-right: 4px;
  flex: 0 0 auto;
}

.sankey-empty {
  height: 100%;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 1rem;
}
</style>
