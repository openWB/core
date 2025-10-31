<template>
  <q-dialog
    v-model="isOpen"
    :maximized="isSmallScreen"
    :backdrop-filter="isSmallScreen ? '' : 'blur(4px)'"
  >
    <q-card>
      <q-card-section>
        <div class="row no-wrap">
          <div class="text-h6 q-pr-sm">Speicher-Beachtung:</div>
          <div class="text-h6 ellipsis" :title="name">{{ name }}</div>
          <q-space />
          <q-btn icon="close" flat round dense v-close-popup />
        </div>
      </q-card-section>
      <q-separator />
      <q-card-section>
        <div class="text-subtitle2">Überschuss primär für:</div>
        <BatteryModeButtons />
      </q-card-section>
    </q-card>
  </q-dialog>
</template>

<script setup lang="ts">
import { computed, ref } from 'vue';
import { Screen } from 'quasar';
import BatteryModeButtons from './BatteryModeButtons.vue';
import { useMqttStore } from 'src/stores/mqtt-store';

const isOpen = ref(false);

const props = defineProps<{
  batteryId: number | undefined;
}>();

const mqttStore = useMqttStore();

const isSmallScreen = computed(() => Screen.lt.sm);

const name = computed(() => {
  if (props.batteryId === undefined || props.batteryId === -1) {
    return 'Übergreifend';
  }
  return mqttStore.batteryName(props.batteryId);
});

defineExpose({
  open: () => (isOpen.value = true),
});
</script>
