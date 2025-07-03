<template>
  <q-scroll-area
    :thumb-style="thumbStyle"
    :bar-style="barStyle"
    class="custom-legend-container"
  >
    <q-list dense class="q-pa-none">
      <div class="row wrap q-pa-none items-center justify-center">
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
      </div>
    </q-list>
  </q-scroll-area>
</template>

<script setup lang="ts">
import { LegendItem } from 'chart.js';

defineProps<{
  items: LegendItem[];
  toggleDataset: (datasetName: string, datasetIndex: number) => void;
  getItemColor: (dataset: LegendItem) => string;
}>();

const thumbStyle = {
  borderRadius: '5px',
  backgroundColor: 'var(--q-primary)',
  width: '6px',
  opacity: '1',
};

const barStyle = {
  borderRadius: '5px',
  backgroundColor: 'var(--q-secondary)',
  width: '6px',
  opacity: '1',
};
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
