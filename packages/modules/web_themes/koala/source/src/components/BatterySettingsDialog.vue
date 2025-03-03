<template>
  <q-dialog
    v-model="isOpen"
    :maximized="$q.screen.width < 385"
    :backdrop-filter="$q.screen.width < 385 ? '' : 'blur(4px)'"
  >
    <q-card style="min-width: 24em">
      <q-card-section>
        <div class="text-h6">{{cardTitle}}</div>
        <div class="text-subtitle2 q-mt-sm">Laden mit Überschuss Modus:</div>
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

const cardTitle = computed(() => {
  if (props.batteryId === undefined) {
    return 'Übergreifende Einstellungen';
  }
  return `Einstellungen ${mqttStore.batteryName(props.batteryId)}`;
});

defineExpose({
  open: () => (isOpen.value = true),
});
</script>
