<template>
  <q-btn-group push rounded class="q-mt-md">
    <q-btn
      v-for="mode in chargeModes"
      :key="mode.value"
      :flat="chargeMode.value !== mode.value"
      :outline="chargeMode.value === mode.value"
      :glossy="chargeMode.value === mode.value"
      :label="mode.label"
      :color="mode.color"
      size="sm"
      @click="chargeMode.value = mode.value"
    />
  </q-btn-group>
</template>

<script setup lang="ts">
import { useMqttStore } from 'src/stores/mqtt-store';
import { computed } from 'vue';

const props = defineProps<{
  chargePointId: number;
}>();

const mqttStore = useMqttStore();

const chargeModes = [
  { value: 'instant_charging', label: 'Sofort', color: 'negative' },
  { value: 'pv_charging', label: 'PV', color: 'positive' },
  { value: 'scheduled_charging', label: 'Ziel', color: 'primary' },
  { value: 'standby', label: 'Standby', color: 'warning' },
  { value: 'stop', label: 'Stop', color: 'light' },
];

const chargeMode = computed(() =>
  mqttStore.chargePointConnectedVehicleChargeMode(props.chargePointId),
);
</script>
