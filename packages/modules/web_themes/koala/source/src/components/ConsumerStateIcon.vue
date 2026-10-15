<template>
  <q-icon
    :name="plugState || notControlled ? 'power' : 'power_off'"
    size="sm"
    :color="color"
  >
    <q-tooltip>
      <div>{{ stateText }}</div>
    </q-tooltip>
  </q-icon>
</template>

<script setup lang="ts">
import { useMqttStore } from 'src/stores/mqtt-store';
import { computed } from 'vue';

const props = defineProps<{
  consumerId: number;
}>();

const mqttStore = useMqttStore();

const plugState = computed(() => mqttStore.consumerPlugState(props.consumerId));

const chargeState = computed(() =>
  mqttStore.consumerChargeState(props.consumerId),
);

// consumers without a relay: plug state only reflects power != 0 W
const notControlled = computed(() => {
  const usageType = mqttStore.consumerUsageType(props.consumerId);
  return usageType === 'meter_only' || usageType === 'self_controlled';
});

const faultState = computed(() =>
  mqttStore.consumerFaultState(props.consumerId),
);

const color = computed(() => {
  if (faultState.value >= 2) {
    return 'negative';
  }
  if (faultState.value === 1) {
    return 'warning';
  }
  if (chargeState.value) {
    return 'positive';
  }
  return plugState.value ? 'warning' : 'grey-6';
});

const stateText = computed(() => {
  if (notControlled.value) {
    return chargeState.value ? 'An' : plugState.value ? 'Standby' : 'Aus';
  }
  if (plugState.value) {
    return chargeState.value ? 'An' : 'Freigegeben, Standby-Modus';
  }
  return chargeState.value ? 'An, nicht von openWB eingeschaltet' : 'Aus';
});
</script>
