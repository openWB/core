<template>
  <q-btn-group class="q-mt-md">
    <q-btn
      v-for="mode in batModes"
      :key="mode.value"
      :color="batMode.value === mode.value ? 'primary' : 'grey'"
      :label="mode.label"
      :icon="mode.icon"
      size="sm"
      @click="batMode.value = mode.value"
    >
      <q-tooltip class="bg-primary">{{ mode.tooltip }}</q-tooltip>
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
    color: 'primary',
    icon: 'directions_car',
    tooltip: 'Auto ',
  },
  {
    value: 'bat_mode',
    label: 'Speicher',
    color: 'primary',
    icon: 'battery_charging_full',
    tooltip: 'Speicher',
  },
  {
    value: 'min_soc_bat_mode',
    label: 'SoC',
    color: 'primary',
    icon: 'battery_charging_full',
    tooltip: 'Minimum Speicher SoC',
  },
];

const batMode = computed(() => mqttStore.batteryMode());
</script>
