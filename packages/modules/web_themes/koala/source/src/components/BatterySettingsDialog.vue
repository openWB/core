<template>
  <q-dialog
    v-model="isOpen"
    :maximized="isSmallScreen"
    :backdrop-filter="isSmallScreen ? '' : 'blur(4px)'"
  >
    <q-card class="card-width">
      <q-card-section>
        <div class="row no-wrap">
          <div>
            <div class="text-h6 q-pr-sm">Speicher-Beachtung:</div>
            <div class="text-h6 ellipsis" :title="name">{{ name }}</div>
          </div>
          <q-space />
          <q-btn
            icon="close"
            flat
            round
            dense
            v-close-popup
            class="close-btn"
          />
        </div>
      </q-card-section>
      <q-separator />
      <q-card-section>
        <div class="text-subtitle2">Ladepriorität:</div>
        <BatteryModeButtons />
          <RangeSliderStandard  v-if="batteryMode === 'min_soc_bat_mode'" class="q-pt-md"
            v-model="batteryRange"
            title="SoC-Grenzen des Speichers % :"
            :min="0"
            :max="100"
            :step="1"
            :markers="10"
          />
      </q-card-section>
    </q-card>
  </q-dialog>
</template>

<script setup lang="ts">
import { computed, ref } from 'vue';
import { Screen } from 'quasar';
import BatteryModeButtons from './BatteryModeButtons.vue';
import RangeSliderStandard from './RangeSliderStandard.vue';
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

const batteryMode = computed(() => mqttStore.batteryMode().value);

const batteryRange = computed({
  get: () => mqttStore.batteryChargePriorityRange,
  set: (value) => {
    mqttStore.batteryChargePriorityRange = value;
  },
});
</script>
<style lang="scss" scoped>
.card-width {
  max-width: 600px;
}
.close-btn {
  height: 2.5em;
  width: 2.5em;
}
</style>
