<template>
  <q-dialog
    v-model="isOpen"
    :maximized="$q.screen.width < 385"
    :backdrop-filter="$q.screen.width < 385 ? '' : 'blur(4px)'"
  >
    <q-card>
      <q-card-section>
        <div class="row">
          <div class="text-h6 q-pr-sm">Einstellungen:</div>
          <div class="text-h6 ellipsis" :title="name">{{ name }}</div>
        </div>
      </q-card-section>
      <q-separator />
      <q-card-section>
        <div class="text-subtitle2">Laden mit Überschuss Modus:</div>
        <BatteryModeButtons />
      </q-card-section>
      <q-card-actions align="right">
        <q-btn flat label="OK" color="primary" v-close-popup />
      </q-card-actions>
    </q-card>
  </q-dialog>
</template>

<script setup lang="ts">
import { computed, ref } from 'vue';
import { useQuasar } from 'quasar';
import BatteryModeButtons from './BatteryModeButtons.vue';
import { useMqttStore } from 'src/stores/mqtt-store';

const $q = useQuasar();
const isOpen = ref(false);

const props = defineProps<{
  batteryId: number | undefined;
}>();

const mqttStore = useMqttStore();

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
