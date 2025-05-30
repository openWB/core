<template>
  <div class="cp-power no-wrap row inline items-center q-gutter-xs">
    <span>{{ power }}</span>
    <q-badge rounded color="primary" :label="(phaseNumber as number)">
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
}>();
</script>

<style scoped>
.cp-power {
  white-space: nowrap;
}
</style>
