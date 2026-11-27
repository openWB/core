<template>
  <q-dialog
    v-model="visible"
    :maximized="isSmallScreen"
    :backdrop-filter="isSmallScreen ? '' : 'blur(4px)'"
    :persistent="dashboard && saving"
  >
    <q-card class="card-width">
      <q-card-section>
        <SettingsDialogHeader
          v-if="dashboard"
          :name="name"
          :saving="saving"
          @close="visible = false"
          @apply="applyChanges"
        />
        <div v-else class="row no-wrap">
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
      <q-card-section :inert="saving || undefined">
        <div class="text-subtitle2">Ladepriorität:</div>
        <BatteryModeButtons />
        <RangeSliderStandard
          v-if="batteryMode === 'min_soc_bat_mode'"
          class="q-pt-md"
          v-model="batteryRange"
          title="SoC-Grenzen des Speichers:"
          :min="0"
          :max="100"
          :step="1"
          :markers="10"
        />
      </q-card-section>
      <SettingsDiscardDialog
        :model-value="confirmClose"
        :saving="saving"
        @discard="discardChanges"
        @apply="applyChanges"
      />
    </q-card>
  </q-dialog>
</template>

<script setup lang="ts">
import { computed, ref } from 'vue';
import { Screen } from 'quasar';
import BatteryModeButtons from './BatteryModeButtons.vue';
import RangeSliderStandard from './RangeSliderStandard.vue';
import { useSettingsDialog } from 'src/composables/useSettingsDialog';
import SettingsDialogHeader from './SettingsDialogHeader.vue';
import SettingsDiscardDialog from './SettingsDiscardDialog.vue';

const isOpen = ref(false);

const props = defineProps<{
  batteryId: number | undefined;
}>();

const {
  dashboard,
  mqttStore,
  visible,
  saving,
  confirmClose,
  discardChanges,
  applyChanges,
} = useSettingsDialog(
  () => isOpen.value,
  (value) => (isOpen.value = value),
);

const isSmallScreen = computed(() => Screen.lt.sm);

const name = computed(() => {
  if (props.batteryId === undefined || props.batteryId === -1) {
    return 'Übergreifend';
  }
  return mqttStore.value.batteryName(props.batteryId);
});

defineExpose({
  open: () => (isOpen.value = true),
});

const batteryMode = computed(() => mqttStore.value.batteryMode().value);

const batteryRange = computed({
  get: () => mqttStore.value.batteryChargePriorityRange,
  set: (value) => {
    mqttStore.value.batteryChargePriorityRange = value;
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
