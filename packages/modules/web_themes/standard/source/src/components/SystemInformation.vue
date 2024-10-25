<template>
  <div>
    <p>{{ title }}</p>
    <p>IP: {{ mqttStore.systemIp }}</p>
    <p>Version: {{ mqttStore.systemVersion }}</p>
    <p>Time: {{ mqttStore.systemDateTime('locale-string') }}</p>
    <p>Theme Configuration: {{ mqttStore.themeConfiguration }}</p>
    <p>
      General getter:
      {{ mqttStore.getValue('openWB/general/web_theme', 'configuration') }}
    </p>
    <p>
      Vehicle List:
      {{ mqttStore.vehicleList() }}
    </p>
  </div>
</template>

<script setup lang="ts">
import { useMqttStore } from 'src/stores/mqtt-store';

const mqttStore = useMqttStore();

interface Props {
  title: string;
}

defineProps<Props>();
</script>
