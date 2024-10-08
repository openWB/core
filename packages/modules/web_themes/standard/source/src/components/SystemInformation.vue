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
    <p>Charge point Names: {{ mqttStore.getChargePointNames }}</p>
  </div>
</template>

<script setup lang="ts">
import { onMounted } from 'vue';
import { useMqttStore } from 'src/stores/mqtt-store';

const mqttStore = useMqttStore();
const topicsToSubscribe = <string[]>['openWB/chargepoint/+/config'];

onMounted(() => {
  // explicit subscriptions are only necessary if subscribing to topics with wildcards
  mqttStore.subscribe(topicsToSubscribe);
});

interface Props {
  title: string;
}

defineProps<Props>();
</script>
