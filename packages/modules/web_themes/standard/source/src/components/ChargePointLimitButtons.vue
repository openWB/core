<template>
  <q-btn-group push rounded class="q-mt-md">
    <q-btn
      v-for="mode in limitModes"
      :key="mode.value"
      :flat="limitMode.value !== mode.value"
      :outline="limitMode.value === mode.value"
      :glossy="limitMode.value === mode.value"
      :label="mode.label"
      :color="mode.color"
      size="sm"
      @click="limitMode.value = mode.value"
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

const limitModes = [
  { value: 'none', label: 'keine', color: 'secondary' },
  { value: 'soc', label: 'EV-SoC', color: 'secondary' },
  { value: 'amount', label: 'Energiemenge', color: 'secondary' },
];

const limitMode = computed(() =>
  mqttStore.chargePointConnectedVehicleInstantChargeLimit(props.chargePointId),
);
</script>
