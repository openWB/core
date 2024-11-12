<template>
  <q-btn-group push rounded class="q-mt-md">
    <q-btn
      v-for="mode in batModes"
      :key="mode.value"
      :flat="batMode.value !== mode.value"
      :outline="batMode.value === mode.value"
      :glossy="batMode.value === mode.value"
      :label="mode.label"
      :icon="mode.icon"
      :color="mode.color"
      size="sm"
      @click="batMode.value = mode.value"
    >
      <q-tooltip class="bg-secondary">{{ mode.tooltip }}</q-tooltip>
    </q-btn>
  </q-btn-group>
</template>

<script setup lang="ts">
import { useMqttStore } from 'src/stores/mqtt-store';
import { computed } from 'vue';

const mqttStore = useMqttStore();

const batModes = [
  {
    value: 'ev_mode',
    label: 'Auto',
    color: 'secondary',
    icon: 'directions_car',
    tooltip: 'Auto ',
  },
  {
    value: 'bat_mode',
    label: 'Speicher',
    color: 'secondary',
    icon: 'battery_charging_full',
    tooltip: 'Speicher',
  },
  {
    value: 'min_soc_bat_mode',
    label: 'SoC',
    color: 'secondary',
    icon: 'battery_charging_full',
    tooltip: 'Minimum Speicher SoC',
  },
];

const batMode = computed(() => mqttStore.batteryMode());
</script>
