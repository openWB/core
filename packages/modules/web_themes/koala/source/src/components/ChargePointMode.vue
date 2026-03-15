<template>
  <q-chip outline size="sm" :color="currentModeColor">{{
    currentModeLabel
  }}</q-chip>
</template>

<script setup lang="ts">
import { computed } from 'vue';
import { useMqttStore } from 'src/stores/mqtt-store';
import { useChargeModes } from 'src/composables/useChargeModes';

const props = defineProps<{
  chargePointId: number;
}>();

const mqttStore = useMqttStore();
const { chargeModes } = useChargeModes();

const chargeMode = computed(() =>
  mqttStore.chargePointConnectedVehicleChargeMode(props.chargePointId),
);

const currentModeLabel = computed(
  () =>
    chargeModes.find((mode) => mode.value === chargeMode.value.value)?.label,
);
const currentModeColor = computed(
  () =>
    chargeModes.find((mode) => mode.value === chargeMode.value.value)?.color,
);
</script>
