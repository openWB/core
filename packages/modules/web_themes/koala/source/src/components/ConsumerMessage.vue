<template>
  <BaseMessage
    :show-message="showMessage"
    :message="message"
    :type="messageType"
  />
</template>

<script setup lang="ts">
import { computed } from 'vue';
import { useMqttStore } from 'src/stores/mqtt-store';
import BaseMessage from './BaseMessage.vue';

const props = defineProps<{
  consumerId: number;
}>();

const mqttStore = useMqttStore();

const faultState = computed(() =>
  mqttStore.consumerFaultState(props.consumerId),
);

const message = computed(() => {
  const text =
    faultState.value > 0
      ? mqttStore.consumerFaultStr(props.consumerId)
      : mqttStore.consumerStateStr(props.consumerId);
  return text ?? '';
});

const showMessage = computed(() => message.value !== '');

const messageType = computed<'info' | 'warning' | 'error'>(() => {
  if (faultState.value >= 2) {
    return 'error';
  }
  if (faultState.value === 1) {
    return 'warning';
  }
  return 'info';
});
</script>
