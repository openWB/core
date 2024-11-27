<template>
  <q-icon
    v-if="props.readonly"
    :name="priority ? icon.on : icon.off"
    :color="priority ? 'warning' : ''"
    size="sm"
  />
  <q-toggle
    v-else
    v-model="priority"
    :color="priority ? 'primary' : ''"
    :checked-icon="icon.on"
    :unchecked-icon="icon.off"
    size="lg"
  />
</template>

<script setup lang="ts">
import { useMqttStore } from 'src/stores/mqtt-store';

const props = defineProps({
  chargePointId: {
    type: Number,
    required: true,
  },
  readonly: {
    type: Boolean,
    default: false,
  },
});

const icon = {
  off: 'star_border',
  on: 'star',
};

const mqttStore = useMqttStore();

const priority = mqttStore.chargePointConnectedVehiclePriority(
  props.chargePointId,
);
</script>
