<template>
  <div
    :class="[
      'text-no-wrap items-center',
      columnDisplayFormat ? 'column' : 'row inline no-wrap',
    ]"
  >
    <span>{{ power }}</span>
    <div :class="{ 'q-ml-xs': !columnDisplayFormat }">
      <q-badge rounded color="primary" :label="phaseNumber" class="q-mr-xs">
        <q-tooltip>Phasenanzahl</q-tooltip>
      </q-badge>
      <span>{{ current }}</span>
    </div>
  </div>
</template>

<script setup lang="ts">
defineProps<{
  power: string;
  phaseNumber: number;
  current: string;
  columnDisplayFormat?: boolean;
}>();
</script>
