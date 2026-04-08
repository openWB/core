<template>
  <div
    v-if="showIcon"
    id="mqtt-connection-indicator"
  >
    <q-badge
      rounded
      align="middle"
      :color="connected ? 'positive' : 'negative'"
      class="non-selectable"
    >
      <q-icon
        :name="connected ? 'link' : 'link_off'"
        size="sm"
      >
        <q-tooltip v-if="connected">Verbindung hergestellt</q-tooltip>
        <q-tooltip v-else>Verbindung getrennt</q-tooltip>
      </q-icon>
    </q-badge>
  </div>
  <q-dialog
    v-model="showModal"
    persistent
  >
    <q-card>
      <q-card-section class="row items-center">
        <q-avatar icon="link_off" color="negative" text-color="white" />
        <span class="text-h6 q-ml-sm">Verbindung getrennt!</span>
      </q-card-section>
      <q-card-section class="row">
        Die Verbindung zur openWB ist unterbrochen.<br />
        Es wird versucht, die Verbindung wieder herzustellen...
      </q-card-section>
    </q-card>
  </q-dialog>
</template>

<script setup lang="ts">
import { computed, watch, ref } from 'vue';
import { useMqttStore } from 'src/stores/mqtt-store';

const mqttStore = useMqttStore();

const connected = computed(() => mqttStore.mqttClientConnected);

const showIcon = ref(!connected.value);
const iconTimeout = ref<ReturnType<typeof setTimeout> | null>(null);
const showModal = computed(() => !connected.value);

watch(connected, (newValue) => {
  if (!newValue) {
    console.warn('MQTT-Verbindung verloren!');
    showIcon.value = true;
    if (iconTimeout.value) {
      clearTimeout(iconTimeout.value);
    }
  } else {
    console.info('MQTT-Verbindung wiederhergestellt!');
    if (iconTimeout.value) {
      clearTimeout(iconTimeout.value);
    }
    iconTimeout.value = setTimeout(() => {
      showIcon.value = false;
    }, 5000);
  }
});
</script>
