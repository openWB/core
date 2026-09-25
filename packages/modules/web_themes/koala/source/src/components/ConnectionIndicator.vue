<template>
  <div v-if="showIcon" id="mqtt-connection-indicator">
    <q-badge
      rounded
      align="middle"
      :color="stateDisplay.color"
      class="non-selectable"
    >
      <q-icon :name="stateDisplay.icon" size="sm">
        <q-tooltip>{{ stateDisplay.tooltip }}</q-tooltip>
      </q-icon>
    </q-badge>
  </div>
  <q-dialog v-model="showModal" persistent>
    <q-card>
      <q-card-section class="row items-center">
        <q-avatar
          :icon="stateDisplay.icon"
          :color="stateDisplay.color"
          text-color="white"
        />
        <span class="text-h6 q-ml-sm">{{ stateDisplay.title }}</span>
      </q-card-section>
      <q-card-section v-if="connectionState === 'connecting'" class="row">
        Die Verbindung zur openWB wird hergestellt.<br />
        Bitte warten...
      </q-card-section>
      <q-card-section
        v-else-if="connectionState === 'disconnected'"
        class="row"
      >
        Die Verbindung zur openWB ist unterbrochen.<br />
        Es wird versucht, die Verbindung wieder herzustellen...
      </q-card-section>
    </q-card>
  </q-dialog>
</template>

<script setup lang="ts">
import { computed, watch, ref, onBeforeUnmount } from 'vue';
import { useMqttStore } from 'src/stores/mqtt-store';

// delay before showing the connecting dialog, prevents flickering on fast connects
const CONNECTING_DIALOG_DELAY = 1000;
// time to wait for a connection before showing the disconnected warning
const CONNECTING_GRACE_PERIOD = 10000;

const mqttStore = useMqttStore();

const connected = computed(() => mqttStore.mqttClientConnected);
const connectingDialogDelayPassed = ref(false);
const connectingTimedOut = ref(false);

const connectionState = computed(() => {
  if (connected.value) {
    return 'connected';
  }
  return connectingTimedOut.value ? 'disconnected' : 'connecting';
});

const stateDisplay = computed(() => {
  switch (connectionState.value) {
    case 'connected':
      return {
        color: 'positive',
        icon: 'link',
        tooltip: 'Verbindung hergestellt',
        title: 'Verbindung hergestellt',
      };
    case 'connecting':
      return {
        color: 'grey',
        icon: 'hourglass_empty',
        tooltip: 'Verbindung wird aufgebaut',
        title: 'Verbindung wird aufgebaut',
      };
    default:
      return {
        color: 'negative',
        icon: 'link_off',
        tooltip: 'Verbindung getrennt',
        title: 'Verbindung getrennt!',
      };
  }
});

const showIcon = ref(!connected.value);
const iconTimeout = ref<ReturnType<typeof setTimeout> | null>(null);
const connectingDialogTimeout = ref<ReturnType<typeof setTimeout> | null>(null);
const connectingTimeout = ref<ReturnType<typeof setTimeout> | null>(null);
const showModal = computed(
  () =>
    connectionState.value === 'disconnected' ||
    (connectionState.value === 'connecting' &&
      connectingDialogDelayPassed.value),
);

const clearConnectingTimeouts = () => {
  if (connectingDialogTimeout.value) {
    clearTimeout(connectingDialogTimeout.value);
    connectingDialogTimeout.value = null;
  }
  if (connectingTimeout.value) {
    clearTimeout(connectingTimeout.value);
    connectingTimeout.value = null;
  }
};

const startConnectingTimeouts = () => {
  clearConnectingTimeouts();
  connectingDialogDelayPassed.value = false;
  connectingTimedOut.value = false;
  connectingDialogTimeout.value = setTimeout(() => {
    connectingDialogDelayPassed.value = true;
  }, CONNECTING_DIALOG_DELAY);
  connectingTimeout.value = setTimeout(() => {
    console.warn('MQTT-Verbindung konnte nicht hergestellt werden!');
    connectingTimedOut.value = true;
  }, CONNECTING_GRACE_PERIOD);
};

if (!connected.value) {
  startConnectingTimeouts();
}

watch(connected, (newValue) => {
  if (!newValue) {
    console.warn('MQTT-Verbindung verloren!');
    showIcon.value = true;
    if (iconTimeout.value) {
      clearTimeout(iconTimeout.value);
    }
    startConnectingTimeouts();
  } else {
    console.info('MQTT-Verbindung wiederhergestellt!');
    clearConnectingTimeouts();
    connectingDialogDelayPassed.value = false;
    connectingTimedOut.value = false;
    if (iconTimeout.value) {
      clearTimeout(iconTimeout.value);
    }
    iconTimeout.value = setTimeout(() => {
      showIcon.value = false;
    }, 5000);
  }
});

onBeforeUnmount(() => {
  clearConnectingTimeouts();
  if (iconTimeout.value) {
    clearTimeout(iconTimeout.value);
  }
});
</script>
