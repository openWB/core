<template>
  <HistoryChartLegendScrollArea
    v-if="chart && !legendLarge"
    :items="legendItems"
    :toggleDataset="toggleDataset"
    :getItemColor="getItemColor"
  />

  <div v-else class="row justify-center items-center">
    <HistoryChartLegendCategory
      :label="'Komponenten Legend'"
      :items="categorizedLegendItems.component"
      :toggleDataset="toggleDataset"
      :getItemColor="getItemColor"
    />

    <HistoryChartLegendCategory
      :label="'Ladepunkt Legend'"
      :items="categorizedLegendItems.chargepoint"
      :toggleDataset="toggleDataset"
      :getItemColor="getItemColor"
    />

    <HistoryChartLegendCategory
      :label="'Fahrzeug Legend'"
      :items="categorizedLegendItems.vehicle"
      :toggleDataset="toggleDataset"
      :getItemColor="getItemColor"
    />

    <HistoryChartLegendCategory
      :label="'Speicher Legend'"
      :items="categorizedLegendItems.battery"
      :toggleDataset="toggleDataset"
      :getItemColor="getItemColor"
    />
  </div>
</template>

<script setup lang="ts">
import { ref, watch, computed, nextTick } from 'vue';
import { useLocalDataStore } from 'src/stores/localData-store';
import { Chart, LegendItem } from 'chart.js';
import type { Category, CategorizedDataset } from './history-chart-model';
import { useMqttStore } from 'src/stores/mqtt-store';
import HistoryChartLegendCategory from './HistoryChartLegendCategory.vue';
import HistoryChartLegendScrollArea from './HistoryChartLegendScrollArea.vue';

const mqttStore = useMqttStore();

const props = defineProps<{
  chart: Chart | null;
}>();

const localDataStore = useLocalDataStore();
const legendItems = ref<LegendItem[]>([]);

const updateLegendItems = () => {
  if (!props.chart) return;

  const items =
    props.chart.options.plugins?.legend?.labels?.generateLabels?.(
      props.chart,
    ) || [];

  items.forEach((item) => {
    if (item.text && localDataStore.isDatasetHidden(item.text)) {
      item.hidden = true;
    }

    //  Inject the category from the dataset
    const dataset = props.chart?.data.datasets[
      item.datasetIndex!
    ] as unknown as CategorizedDataset;
    (item as LegendItem & { category?: Category }).category = dataset.category;
  });

  legendItems.value = items;
  console.log('legendItems:', legendItems.value);
};

const categorizedLegendItems = computed(() => {
  const categories: Record<Category, LegendItem[]> = {
    chargepoint: [],
    vehicle: [],
    battery: [],
    component: [],
  };
  for (const item of legendItems.value) {
    const category = (item as LegendItem & { category?: Category }).category;
    if (category && categories[category]) {
      categories[category].push(item);
    } else {
      categories.component.push(item);
    }
  }
  // Sort each category's items alphabetically
  Object.keys(categories).forEach((key) => {
    categories[key as Category].sort((a, b) =>
      (a.text || '').localeCompare(b.text || ''),
    );
  });
  return categories;
});

const legendLarge = computed(() => {
  return legendItems.value.length > 100;
});

const getItemColor = (item: LegendItem) => {
  if (!props.chart || item.datasetIndex === undefined) return '#ccc';

  const dataset = props.chart.data.datasets[item.datasetIndex];
  return (dataset.borderColor as string) || '#ccc';
};

const toggleDataset = (datasetName?: string, datasetIndex?: number) => {
  if (!props.chart || !datasetName || datasetIndex === undefined) return;
  localDataStore.toggleDataset(datasetName);
  if (localDataStore.isDatasetHidden(datasetName)) {
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
        if (
          typeof dataset.label === 'string' &&
          localDataStore.isDatasetHidden(dataset.label)
        ) {
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
