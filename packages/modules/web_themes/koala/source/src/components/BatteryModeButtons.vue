<template>
  <q-btn-group class="q-mt-md">
    <q-btn
      v-for="mode in batteryModes"
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
import { useBatteryModes } from 'src/composables/useBatteryModes.ts';

const mqttStore = useMqttStore();

const { batteryModes } = useBatteryModes();

const batMode = computed(() => mqttStore.batteryMode());
</script>
