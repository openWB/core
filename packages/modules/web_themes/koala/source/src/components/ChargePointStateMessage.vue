<template>
  <div
    class="row q-mt-sm q-pa-sm bg-primary text-white no-wrap message-text"
    color="primary"
    style="border-radius: 10px"
  >
    <q-icon name="info" size="sm" class="q-mr-xs" />
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

const message = computed(() =>
  mqttStore.chargePointStateMessage(props.chargePointId),
);
</script>

<style scoped>
.message-text {
  overflow-x: auto;
  overflow-y: auto;
}
</style>
