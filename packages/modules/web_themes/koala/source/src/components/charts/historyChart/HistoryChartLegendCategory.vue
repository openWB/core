<template>
  <div class="row justify-center items-center">

  </div>
</template>

<script setup lang="ts">
import { ref, watch } from 'vue';
import { useLocalDataStore } from 'src/stores/localData-store';
import { Chart, LegendItem } from 'chart.js';

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
  });
  legendItems.value = items;
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

