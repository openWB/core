<template>
  <q-icon
    :name="plugState ? 'power' : 'power_off'"
    size="sm"
    :color="plugState ? (chargeState ? 'positive' : 'warning') : 'negative'"
  >
    <q-tooltip>
      {{
        plugState
          ? chargeState
            ? 'Lädt'
            : 'Angesteckt, lädt nicht'
          : 'Nicht angesteckt'
      }}
    </q-tooltip>
  </q-icon>
</template>

<script setup lang="ts">
import { useMqttStore } from 'src/stores/mqtt-store';
import { computed } from 'vue';

const props = defineProps<{
  chargePointId?: number;
  vehicleId?: number;
}>();

const mqttStore = useMqttStore();

const plugState = computed(() => {
  if (props.vehicleId !== undefined) {
    const vehicleState = mqttStore.vehicleConnectionState(props.vehicleId);
    return vehicleState.some((v) => v.plugged);
  } else if (props.chargePointId !== undefined) {
    return mqttStore.chargePointPlugState(props.chargePointId);
  }
  return false;
});

const chargeState = computed(() => {
  if (props.vehicleId !== undefined) {
    const vehicleState = mqttStore.vehicleConnectionState(props.vehicleId);
    return vehicleState.some((v) => v.charging);
  } else if (props.chargePointId !== undefined) {
    return mqttStore.chargePointChargeState(props.chargePointId);
  }
  return false;
});
</script>
