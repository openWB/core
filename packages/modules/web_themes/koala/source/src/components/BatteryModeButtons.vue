<template>
  <q-btn-group class="q-mt-md" outline>
    <q-btn
      v-for="mode in batteryModes"
      :key="mode.value"
      :color="batMode.value === mode.value ? 'primary' : 'grey'"
      :outline="batMode.value !== mode.value"
      size="sm"
      @click="batMode.value = mode.value"
    >
      <q-icon :name="mode.icon" />
      <template v-if="mode.value === 'ev_mode'">
        <span class="q-mx-xs">/</span>
        <q-icon name="power" />
      </template>
      <span class="q-ml-xs">{{ mode.label }}</span>
      <q-tooltip class="bg-primary">{{ mode.tooltip }}</q-tooltip>
    </q-btn>
  </q-btn-group>
</template>

<script setup lang="ts">
import { useMqttStore } from 'src/stores/mqtt-store';
import { computed } from 'vue';
import { useBatteryModes } from 'src/composables/useBatteryModes';

const mqttStore = useMqttStore();

const { batteryModes } = useBatteryModes();

const batMode = computed(() => mqttStore.batteryMode());
</script>
