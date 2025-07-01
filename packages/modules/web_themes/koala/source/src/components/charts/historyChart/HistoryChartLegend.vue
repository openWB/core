<template>
  <div class="row justify-center items-center">
  <q-btn-dropdown flat no-caps dense color="primary" label="Legend: Komponenten" class="q-mr-sm">
    <q-list dense class="q-pa-none" style="max-height: 200px; overflow-y: auto;">
        <q-item
          v-for="(dataset, index) in categorizedLegendItems.component"
          :key="dataset.text || index"
          clickable
          dense
          class="q-py-none"
          :class="{ 'legend-item-hidden': dataset.hidden }"
          @click="toggleDataset(dataset.text, dataset.datasetIndex)"
        >
          <q-item-section avatar class="q-pr-none">
            <div
              class="legend-color-box q-mr-sm"
              :style="{ backgroundColor: getItemColor(dataset) }"
            ></div>
          </q-item-section>
          <q-item-section>
            <q-item-label class="text-caption">{{ dataset.text }}</q-item-label>
          </q-item-section>
        </q-item>
    </q-list>

  </q-btn-dropdown>

  <q-btn-dropdown flat no-caps dense color="primary" label="Legend: Ladepunkte" class="q-mr-sm">
    <q-list dense class="q-pa-none" style="max-height: 200px; overflow-y: auto;">
        <q-item
          v-for="(dataset, index) in categorizedLegendItems.chargepoint"
          :key="dataset.text || index"
          clickable
          dense
          class="q-py-none"
          :class="{ 'legend-item-hidden': dataset.hidden }"
          @click="toggleDataset(dataset.text, dataset.datasetIndex)"
        >
          <q-item-section avatar class="q-pr-none">
            <div
              class="legend-color-box q-mr-sm"
              :style="{ backgroundColor: getItemColor(dataset) }"
            ></div>
          </q-item-section>
          <q-item-section>
            <q-item-label class="text-caption">{{ dataset.text }}</q-item-label>
          </q-item-section>
        </q-item>
    </q-list>

  </q-btn-dropdown>

  <q-btn-dropdown flat no-caps dense color="primary" label="Legend: Fahrzeuge" class="q-mr-sm">
    <q-list dense class="q-pa-none" style="max-height: 200px; overflow-y: auto;">
        <q-item
          v-for="(dataset, index) in categorizedLegendItems.vehicle"
          :key="dataset.text || index"
          clickable
          dense
          class="q-py-none"
          :class="{ 'legend-item-hidden': dataset.hidden }"
          @click="toggleDataset(dataset.text, dataset.datasetIndex)"
        >
          <q-item-section avatar class="q-pr-none">
            <div
              class="legend-color-box q-mr-sm"
              :style="{ backgroundColor: getItemColor(dataset) }"
            ></div>
          </q-item-section>
          <q-item-section>
            <q-item-label class="text-caption">{{ dataset.text }}</q-item-label>
          </q-item-section>
        </q-item>
    </q-list>

  </q-btn-dropdown>

  <q-btn-dropdown flat no-caps dense color="primary" label="Legend: Speicher" class="q-mr-sm">
    <q-list dense class="q-pa-none" style="max-height: 200px; overflow-y: auto;">
        <q-item
          v-for="(dataset, index) in categorizedLegendItems.battery"
          :key="dataset.text || index"
          clickable
          dense
          class="q-py-none"
          :class="{ 'legend-item-hidden': dataset.hidden }"
          @click="toggleDataset(dataset.text, dataset.datasetIndex)"
        >
          <q-item-section avatar class="q-pr-none">
            <div
              class="legend-color-box q-mr-sm"
              :style="{ backgroundColor: getItemColor(dataset) }"
            ></div>
          </q-item-section>
          <q-item-section>
            <q-item-label class="text-caption">{{ dataset.text }}</q-item-label>
          </q-item-section>
        </q-item>
    </q-list>

  </q-btn-dropdown>
  </div>
</template>

<script setup lang="ts">
import { ref, watch, computed } from 'vue';
import { useLocalDataStore } from 'src/stores/localData-store';
import { Chart, LegendItem } from 'chart.js';
import type {
  Category,
  CategorizedDataset,
} from './history-chart-model';
import { useMqttStore } from 'src/stores/mqtt-store';

const mqttStore = useMqttStore();

const props = defineProps<{
  chart: Chart | null;
}>();

const localDataStore = useLocalDataStore();
const legendItems = ref<LegendItem[]>([]);

const updateLegendItems = () => {
  if (!props.chart) return;

  const items = props.chart.options.plugins?.legend?.labels?.generateLabels?.(
    props.chart
  ) || [];

  items.forEach((item) => {
    if (item.text && localDataStore.isDatasetHidden(item.text)) {
      item.hidden = true;
    }

    //  Inject the category from the dataset
    const dataset = props.chart?.data.datasets[item.datasetIndex!] as unknown as CategorizedDataset;
    (item as LegendItem & { category?: Category }).category = dataset.category;
  });

  legendItems.value = items;
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
  // Sort each category's items alphabetically by text
  Object.keys(categories).forEach((key) => {
    categories[key as Category].sort((a, b) =>
      (a.text || '').localeCompare(b.text || '')
    );
  });
  console.log('Categorized Legend Items:', categories);
  return categories;
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
  () => {
    updateLegendItems();
  },
);


// const thumbStyle = {
//   borderRadius: '5px',
//   backgroundColor: 'var(--q-primary)',
//   width: '6px',
//   opacity: '1',
// };

// const barStyle = {
//   borderRadius: '5px',
//   backgroundColor: 'var(--q-secondary)',
//   width: '6px',
//   opacity: '1',
// };
</script>

<style scoped>
.custom-legend-container {
  margin-bottom: 5px;
  height: 70px;
  border-radius: 5px;
  text-align: left;
  width: 100%;
}

.legend-color-box {
  display: inline-block;
  width: 20px;
  height: 3px;
}

.legend-item-hidden {
  opacity: 0.6 !important;
  text-decoration: line-through !important;
}

/* Override the avatar section min-width */
:deep(.q-item__section--avatar) {
  min-width: 5px !important;
  padding-right: 0px !important;
}

/* For very small screens */
@media (max-width: 576px) {
  .legend-color-box {
    width: 10px;
    height: 2px;
  }
}
</style>
