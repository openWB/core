<template>
  <BaseMessage
  :show="showMessage"
  :message="message"
  :type="messageType"
/>
</template>

<script setup lang="ts">
import { useMqttStore } from 'src/stores/mqtt-store';
import BaseMessage from './BaseMessage.vue';
import { computed } from 'vue';

const props = defineProps<{
  chargePointId: number;
  faultMessage?: boolean;
}>();
const mqttStore = useMqttStore();


const showMessage = computed(() => {
  return state.value !== undefined && state.value !== 0;
});

const state = computed(() =>
  props.faultMessage
    ? mqttStore.chargePointFaultState(props.chargePointId)
    : -1,
);

const message = computed(() => {
  const message = props.faultMessage
    ? mqttStore.chargePointFaultMessage(props.chargePointId)
    : mqttStore.chargePointStateMessage(props.chargePointId);
  return message ?? '';
});

const messageType = computed(() => {
  switch (state.value) {
    case 1:
      return 'warning';
    case 2:
      return 'error';
    default:
      return 'info';
  }
});
</script>
