<template>
  <q-icon
    :name="locked ? 'lock' : 'lock_open'"
    size="sm"
    :color="locked ? 'red' : 'green'"
    @click="locked = !locked"
    style="cursor: pointer"
    class="q-ml-sm"
  />
</template>

<script setup lang="ts">
import { useMqttStore } from 'src/stores/mqtt-store';
// import { computed } from 'vue';

const props = defineProps<{
  chargePointId: number;
}>();

const mqttStore = useMqttStore();

const locked = mqttStore.chargePointManualLock(props.chargePointId);
</script>
