<template>
  <q-icon
    v-if="props.readonly"
    :name="timeChargingEnabled ? icon.on : icon.off"
    :color="timeChargingEnabled ? 'primary' : ''"
    :size="props.iconSize ? props.iconSize : 'sm'"
  >
    <q-tooltip v-if="props.toolTip">{{
      timeChargingEnabled ? 'Zeitladen aktiviert' : 'Zeitladen deaktiviert'
    }}</q-tooltip>
  </q-icon>
  <q-toggle
    v-else
    v-model="timeChargingEnabled"
    :color="timeChargingEnabled ? 'primary' : ''"
    :checked-icon="icon.on"
    :unchecked-icon="icon.off"
    size="lg"
    :dense="props.dense"
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
  dense: {
    type: Boolean,
    default: false,
  },
  iconSize: {
    type: String,
    default: 'sm',
  },
  toolTip: {
    type: Boolean,
    default: false,
  },
});

const icon = {
  off: 'alarm_off',
  on: 'alarm',
};

const mqttStore = useMqttStore();

const timeChargingEnabled = mqttStore.chargePointConnectedVehicleTimeCharging(
  props.chargePointId,
);
</script>
