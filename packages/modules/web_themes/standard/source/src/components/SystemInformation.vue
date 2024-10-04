<template>
  <div>
    <p>{{ title }}</p>
    <p>IP: {{ mqttStore.topics['openWB/system/ip_address'] }}</p>
    <p>Version: {{ mqttStore.topics['openWB/system/version'] }}</p>
    <p>Time: {{ mqttStore.getSystemTime }}</p>
  </div>
</template>

<script setup lang="ts">
// import { computed, ref } from 'vue';
import { onMounted } from 'vue';
import { useMqttStore } from 'src/stores/mqtt-store';

const mqttStore = useMqttStore();
const topicsToSubscribe = <string[]>[
  'openWB/system/ip_address',
  'openWB/system/time',
  'openWB/system/version',
];

onMounted(() => {
  mqttStore.subscribe(topicsToSubscribe);
});

interface Props {
  title: string;
}

defineProps<Props>();
</script>
