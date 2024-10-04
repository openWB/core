<template>
  <router-view />
</template>

<script setup lang="ts">
import { useMqttStore } from './stores/mqtt-store';

const mqttStore = useMqttStore();
mqttStore.initialize();

defineOptions({
  name: 'OpenwbStandardWebTheme',
});
</script>
