<template>
  <div
    v-if="state !== undefined && state !== 0"
    class="row q-mt-md q-pa-sm text-white"
    :class="messageClass"
    style="border-radius: 10px"
  >
    {{ message }}
  </div>
</template>

<script setup lang="ts">
import { useMqttStore } from 'src/stores/mqtt-store';
import { computed } from 'vue';

const props = defineProps<{
  chargePointId: number;
}>();

const mqttStore = useMqttStore();

const state = computed(() =>
  mqttStore.chargePointFaultState(props.chargePointId),
);
const message = computed(() =>
  mqttStore.chargePointFaultMessage(props.chargePointId),
);

const messageClass = computed(() => {
  switch (state.value) {
    case 1:
      return 'bg-warning';
    case 2:
      return 'bg-negative';
    default:
      return 'bg-primary';
  }
});
</script>
