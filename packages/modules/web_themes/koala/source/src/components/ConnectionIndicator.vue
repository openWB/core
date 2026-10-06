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
const dialogDelayPassed = ref(false);
const gracePeriodExpired = ref(false);

const connectionState = computed(() => {
  if (connected.value) {
    return 'connected';
  }
  return gracePeriodExpired.value ? 'disconnected' : 'connecting';
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

const showIcon = ref(false);
const iconHideTimer = ref<ReturnType<typeof setTimeout> | null>(null);
const dialogDelayTimer = ref<ReturnType<typeof setTimeout> | null>(null);
const gracePeriodTimer = ref<ReturnType<typeof setTimeout> | null>(null);
const showModal = computed(
  () =>
    connectionState.value === 'disconnected' ||
    (connectionState.value === 'connecting' && dialogDelayPassed.value),
);

const clearConnectingTimers = () => {
  if (dialogDelayTimer.value) {
    clearTimeout(dialogDelayTimer.value);
    dialogDelayTimer.value = null;
  }
  if (gracePeriodTimer.value) {
    clearTimeout(gracePeriodTimer.value);
    gracePeriodTimer.value = null;
  }
};

const startConnectingTimers = () => {
  clearConnectingTimers();
  dialogDelayPassed.value = false;
  gracePeriodExpired.value = false;
  dialogDelayTimer.value = setTimeout(() => {
    dialogDelayPassed.value = true;
  }, CONNECTING_DIALOG_DELAY);
  gracePeriodTimer.value = setTimeout(() => {
    console.warn('MQTT-Verbindung konnte nicht hergestellt werden!');
    gracePeriodExpired.value = true;
  }, CONNECTING_GRACE_PERIOD);
};

watch(
  connected,
  (newValue, oldValue) => {
    if (!newValue) {
      if (oldValue !== undefined) {
        console.warn('MQTT-Verbindung verloren!');
      }
      showIcon.value = true;
      if (iconHideTimer.value) {
        clearTimeout(iconHideTimer.value);
      }
      startConnectingTimers();
    } else if (oldValue !== undefined) {
      console.info('MQTT-Verbindung wiederhergestellt!');
      clearConnectingTimers();
      dialogDelayPassed.value = false;
      gracePeriodExpired.value = false;
      if (iconHideTimer.value) {
        clearTimeout(iconHideTimer.value);
      }
      iconHideTimer.value = setTimeout(() => {
        showIcon.value = false;
      }, 5000);
    }
  },
  { immediate: true },
);

onBeforeUnmount(() => {
  clearConnectingTimers();
  if (iconHideTimer.value) {
    clearTimeout(iconHideTimer.value);
  }
});
</script>
