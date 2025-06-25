<template>
  <div
    :class="[
      'cp-power items-center q-gutter-xs',
      columnDisplayFormat ? 'column' : 'row inline',
    ]"
  >
    <span>{{ power }}</span>
    <q-badge rounded color="primary" :label="phaseNumber">
      <q-tooltip>Phasenanzahl</q-tooltip>
    </q-badge>
    <span>{{ current }}</span>
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

<style scoped>
.cp-power {
  white-space: nowrap;
}
</style>
