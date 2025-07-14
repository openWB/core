<template>
  <q-list class="q-pa-none">
    <div class="row wrap q-pa-none items-center justify-center">
      <q-item v-for="(dataset, index) in items" :key="dataset.text || index" clickable dense class="q-py-none"
        :class="{ 'legend-item-hidden': dataset.hidden }" @click="
          dataset.datasetIndex !== undefined &&
          toggleDataset(dataset.text, dataset.datasetIndex)
          ">
        <q-item-section avatar class="q-pr-none">
          <svg v-if="getItemLineType(dataset) === 'dashed'" width="20" height="3">
            <line x1="0" y1="1.5" x2="20" y2="1.5" :stroke="getItemColor(dataset)" stroke-width="2"
              stroke-dasharray="8,2" />
          </svg>
          <svg v-else width="20" height="3">
            <line x1="0" y1="1.5" x2="30" y2="1.5" :stroke="getItemColor(dataset)" stroke-width="2" />
          </svg>
        </q-item-section>
        <q-item-section>
          <q-item-label class="text-caption">{{ dataset.text }}</q-item-label>
        </q-item-section>
      </q-item>
    </div>
  </q-list>
</template>

<script setup lang="ts">
import { LegendItem } from 'chart.js';

defineProps<{
  items: LegendItem[];
  toggleDataset: (datasetName: string, datasetIndex: number) => void;
  getItemColor: (dataset: LegendItem) => string;
  getItemLineType: (dataset: LegendItem) => string | undefined;
}>();
</script>

<style scoped>
.legend-item-hidden {
  opacity: 0.6 !important;
  text-decoration: line-through !important;
}

/* Override the avatar section min-width */
.q-item__section--avatar {
  min-width: 5px !important;
  padding-right: 5px !important;
}

.q-item {
  min-height: 22px !important;
  padding-left: 4px !important;
  padding-right: 4px !important;
}

.body--dark .q-list {
  background-color: transparent;
}
</style>
