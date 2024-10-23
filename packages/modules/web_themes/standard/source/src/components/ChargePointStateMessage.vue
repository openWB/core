<template>
  <div
    class="row q-mt-md q-pa-sm bg-primary text-white"
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

const message = computed(() =>
  mqttStore.chargePointStateMessage(props.chargePointId),
);
</script>
