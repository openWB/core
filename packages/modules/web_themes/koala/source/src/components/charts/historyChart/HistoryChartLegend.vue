<template>
  <!-- On smaller screens (<md) always show categories -->
  <HistoryChartLegendCategoriesGroup
    v-if="$q.screen.lt.md"
    :categorizedLegendItems="categorizedLegendItems"
    :toggleDataset="toggleDataset"
    :getItemColor="getItemColor"
    :getItemLineType="getItemLineType"
  />

  <!-- On larger screens: show standard legend if legend not large; otherwise show categories -->
  <HistoryChartLegendStandard
    v-else-if="chart && !$q.screen.lt.sm && !legendLarge"
    :items="legendItems"
    :toggleDataset="toggleDataset"
    :getItemColor="getItemColor"
    :getItemLineType="getItemLineType"
  />

  <HistoryChartLegendCategoriesGroup
    v-else
    :categorizedLegendItems="categorizedLegendItems"
    :toggleDataset="toggleDataset"
    :getItemColor="getItemColor"
    :getItemLineType="getItemLineType"
  />
</template>

<script setup lang="ts">
import { ref, watch, computed, nextTick } from 'vue';
import { useLocalDataStore } from 'src/stores/localData-store';
import { Chart, ChartDataset, LegendItem } from 'chart.js';
import {
  CONSUMER_TOTAL_KEY,
  BATTERY_TOTAL_KEY,
  BATTERY_SOC_KEY,
  type Category,
  type CategorizedDataset,
  type LegendItemWithCategory,
} from './history-chart-model';
import { useMqttStore } from 'src/stores/mqtt-store';
import { useQuasar } from 'quasar';
import HistoryChartLegendCategoriesGroup from './HistoryChartLegendCategoriesGroup.vue';
import HistoryChartLegendStandard from './HistoryChartLegendStandard.vue';

const mqttStore = useMqttStore();
const $q = useQuasar();

const props = defineProps<{
  chart: Chart | null;
}>();

const localDataStore = useLocalDataStore();
const legendItems = ref<LegendItemWithCategory[]>([]);

const legendLarge = computed(() => {
  return legendItems.value.length > 20;
});

const batteryConfigured = computed(() => {
  return mqttStore.batteryConfigured;
});

const updateLegendItems = () => {
  if (!props.chart) return;
  let items = (props.chart.options.plugins?.legend?.labels?.generateLabels?.(
    props.chart,
  ) || []) as LegendItemWithCategory[];
  items.forEach((item) => {
    // Inject the category and key from the dataset
    const dataset = props.chart?.data.datasets[
      item.datasetIndex!
    ] as unknown as CategorizedDataset;
    item.category = dataset.category;
    item.key = dataset.key;
    if (item.key && localDataStore.isDatasetHidden(item.key)) {
      item.hidden = true;
    }
  });
  if (!batteryConfigured.value) {
    items = items.filter(
      (item) => item.key !== BATTERY_TOTAL_KEY && item.key !== BATTERY_SOC_KEY,
    );
  }
  legendItems.value = items;
};

const categorizedLegendItems = computed(() => {
  const categories: Record<Category, LegendItemWithCategory[]> = {
    chargepoint: [],
    vehicle: [],
    battery: [],
    consumer: [],
    component: [],
  };
  for (const item of legendItems.value) {
    const category = item.category;
    if (category && categories[category]) {
      categories[category].push(item);
    } else {
      categories.component.push(item);
    }
  }

  Object.keys(categories).forEach((key) => {
    const category = key as Category;
    categories[category].sort((a, b) =>
      (a.text || '').localeCompare(b.text || '', undefined, {
        numeric: true,
      }),
    );

    if (category === 'consumer') {
      const totalIndex = categories[category].findIndex(
        (item) => item.key === CONSUMER_TOTAL_KEY,
      );
      if (totalIndex > 0) {
        const [total] = categories[category].splice(totalIndex, 1);
        categories[category].unshift(total);
      }
    }
  });
  return categories;
});

const getItemColor = (item: LegendItem): string => {
  if (!props.chart || item.datasetIndex === undefined) return '#ccc';
  const dataset = props.chart.data.datasets[item.datasetIndex];
  return (dataset.borderColor as string) || '#ccc';
};

const getItemLineType = (item: LegendItem) => {
  if (!props.chart || item.datasetIndex === undefined) return;
  const dataset = props.chart.data.datasets[
    item.datasetIndex
  ] as ChartDataset<'line'>;
  const borderDash = dataset.borderDash;
  return Array.isArray(borderDash) && borderDash.length > 0
    ? 'dashed'
    : 'solid';
};

const toggleDataset = (datasetKey?: string, datasetIndex?: number) => {
  if (!props.chart || !datasetKey || datasetIndex === undefined) return;
  localDataStore.toggleDataset(datasetKey);
  if (localDataStore.isDatasetHidden(datasetKey)) {
    props.chart.hide(datasetIndex);
  } else {
    props.chart.show(datasetIndex);
  }
  updateLegendItems();
  props.chart.update();
};

watch(
  () => props.chart,
  (newChart) => {
    if (newChart) {
      newChart.data.datasets.forEach((dataset, index) => {
        const { key } = dataset as unknown as CategorizedDataset;
        if (key && localDataStore.isDatasetHidden(key)) {
          newChart.hide(index);
        }
      });
      newChart.update();
      updateLegendItems();
    }
  },
  { immediate: true },
);

watch(
  () => mqttStore.vehicleList,
  async () => {
    await nextTick();
    updateLegendItems();
  },
);
</script>
