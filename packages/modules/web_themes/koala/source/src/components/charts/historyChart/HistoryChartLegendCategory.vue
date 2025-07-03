<template>
  <q-btn-dropdown
    flat
    no-caps
    dense
    color="primary"
    :label="label"
    class="q-mr-sm"
  >
    <q-list dense class="q-pa-none" style="max-height: 200px; overflow-y: auto">
      <q-item
        v-for="(dataset, index) in items"
        :key="dataset.text || index"
        clickable
        dense
        class="q-py-none"
        :class="{ 'legend-item-hidden': dataset.hidden }"
        @click="
          dataset.datasetIndex !== undefined &&
            toggleDataset(dataset.text, dataset.datasetIndex)
        "
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
</template>

<script setup lang="ts">
import { LegendItem } from 'chart.js';

defineProps<{
  label: string;
  items: LegendItem[];
  toggleDataset: (datasetName: string, datasetIndex: number) => void;
  getItemColor: (dataset: LegendItem) => string;
}>();
</script>

<style scoped>
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
