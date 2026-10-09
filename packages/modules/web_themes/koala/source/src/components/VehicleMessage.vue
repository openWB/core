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
  vehicleId: number;
}>();

const mqttStore = useMqttStore();

const faultState = computed(() => mqttStore.vehicleFaultState(props.vehicleId));

const message = computed(
  () => mqttStore.vehicleFaultMessage(props.vehicleId) ?? '',
);

const showMessage = computed(
  () => faultState.value > 0 && message.value !== '',
);

const messageType = computed<'info' | 'warning' | 'error'>(() =>
  faultState.value >= 2 ? 'error' : 'warning',
);
</script>
