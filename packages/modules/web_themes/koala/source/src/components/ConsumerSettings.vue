<template>
  <q-dialog v-model="visible" :persistent="dashboard && saving">
    <q-card class="dialog-width">
      <q-card-section>
        <SettingsDialogHeader
          v-if="dashboard"
          :name="name"
          :saving="saving"
          @close="visible = false"
          @apply="applyChanges"
        />
        <div v-else class="row items-center no-wrap">
          <div class="text-h6 ellipsis">Einstellungen {{ name }}</div>
          <q-space />
          <q-btn icon="close" flat round dense v-close-popup />
        </div>
      </q-card-section>

      <template v-if="showModeControls">
        <q-separator />

        <q-card-section :inert="saving || undefined">
          <div class="text-subtitle2">Betriebsmodus</div>
          <ConsumerModeButtons :consumer-id="props.consumerId" />
        </q-card-section>

        <q-separator inset />

        <q-card-section :inert="saving || undefined">
          <div class="row items-center justify-between">
            <div class="text-subtitle2 q-mr-sm">Betriebsmodus umstellen</div>
            <ToggleStandard
              :model-value="resetEnabled"
              :size="'sm'"
              color="positive"
              @update:model-value="setResetEnabled"
            />
          </div>

          <template v-if="resetEnabled">
            <q-separator inset class="q-mt-sm" />
            <q-input v-model="resetTime" type="time" label="Uhrzeit" />

            <div class="text-subtitle2 q-mt-md">Wiederholung</div>
            <q-btn-group spread outline class="q-mt-sm">
              <q-btn
                v-for="mode in resetModes"
                :key="mode.value"
                size="sm"
                :outline="resetMode !== mode.value"
                :color="resetMode === mode.value ? 'primary' : 'grey'"
                :label="mode.label"
                @click="selectResetMode(mode.value)"
              />
            </q-btn-group>

            <q-input
              v-if="resetMode === 'once'"
              v-model="resetOnceDate"
              type="date"
              label="Datum"
              class="q-mt-sm"
            />

            <div
              v-if="resetMode === 'weekly'"
              class="row items-center q-gutter-sm justify-center q-mt-xs"
            >
              <div v-for="(day, index) in weekDays" :key="day">
                <q-btn
                  round
                  :size="$q.platform.is.mobile ? '0.8rem' : '0.7rem'"
                  :flat="!resetWeeklyDays[index]"
                  :outline="resetWeeklyDays[index]"
                  color="primary"
                  :label="day"
                  :class="{ deselected: !resetWeeklyDays[index] }"
                  @click="toggleWeeklyDay(index)"
                />
              </div>
            </div>

            <div class="text-subtitle2 q-mt-md">Zielmodus</div>
            <q-btn-group spread outline class="q-mt-sm">
              <q-btn
                v-for="mode in chargeModes"
                :key="mode.value"
                size="sm"
                :outline="resetTargetMode !== mode.value"
                :color="resetTargetMode === mode.value ? 'primary' : 'grey'"
                :label="mode.label"
                @click="resetTargetMode = mode.value"
              />
            </q-btn-group>
          </template>
        </q-card-section>
      </template>

      <q-separator />
      <q-card-actions align="right" :inert="saving || undefined">
        <q-btn
          flat
          dense
          no-caps
          icon="tune"
          label="Geräte-Einstellungen"
          type="a"
          href="/openWB/web/settings/#/ConsumerConfiguration"
          :title="`Geräte-Einstellungen ${name ?? ''}`"
          @click="openDeviceSettings"
        />
      </q-card-actions>
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
import { useSettingsDialog } from 'src/composables/useSettingsDialog';
import { useChargeModes } from 'src/composables/useChargeModes';
import type { ConsumerResetTrigger } from 'src/stores/mqtt-store-model';
import ConsumerModeButtons from './ConsumerModeButtons.vue';
import ToggleStandard from './ToggleStandard.vue';
import SettingsDialogHeader from './SettingsDialogHeader.vue';
import SettingsDiscardDialog from './SettingsDiscardDialog.vue';

const props = defineProps<{
  consumerId: number;
  modelValue: boolean;
}>();

const emit = defineEmits<{
  'update:modelValue': [value: boolean];
}>();

const deviceSettingsRequested = ref(false);
const {
  dashboard,
  mqttStore,
  field,
  visible,
  saving,
  confirmClose,
  discardChanges,
  applyChanges,
} = useSettingsDialog(
  () => props.modelValue,
  (value) => {
    emit('update:modelValue', value);
    if (!value && deviceSettingsRequested.value) {
      deviceSettingsRequested.value = false;
      window.location.assign('/openWB/web/settings/#/ConsumerConfiguration');
    }
  },
);
const { chargeModes } = useChargeModes();

const name = computed(() => mqttStore.value.consumerName(props.consumerId));

function openDeviceSettings(event: Event) {
  if (!dashboard.value) return;
  event.preventDefault();
  deviceSettingsRequested.value = true;
  visible.value = false;
}

const resetModes: { value: ConsumerResetTrigger; label: string }[] = [
  { value: 'once', label: 'Einmalig' },
  { value: 'daily', label: 'Täglich' },
  { value: 'weekly', label: 'Wöchentlich' },
];

const resetEnabled = field((store) =>
  store.consumerResetEnabled(props.consumerId),
);
const resetMode = field((store) =>
  store.consumerResetTrigger(props.consumerId),
);
const resetTargetMode = field((store) =>
  store.consumerResetTargetMode(props.consumerId),
);
const resetTime = field((store) => store.consumerResetTime(props.consumerId));
const resetOnceDate = field((store) =>
  store.consumerResetOnceDate(props.consumerId),
);
const resetWeeklyDays = field((store) =>
  store.consumerResetWeeklyDays(props.consumerId),
);
const weekDays = ['Mo', 'Di', 'Mi', 'Do', 'Fr', 'Sa', 'So'];

const defaultWeekdayIndex = () => {
  // JS: 0=Sonntag ... 6=Samstag, UI: 0=Montag ... 6=Sonntag
  return (new Date().getDay() + 6) % 7;
};

const setResetEnabled = (enabled: boolean) => {
  resetEnabled.value = enabled;
  if (!enabled) {
    return;
  }
  if (!resetTime.value) {
    resetTime.value = '00:00';
  }
  if (!resetTargetMode.value) {
    resetTargetMode.value = 'scheduled_charging';
  }
  if (resetMode.value === 'weekly' && !resetWeeklyDays.value.some(Boolean)) {
    const updated = [...resetWeeklyDays.value];
    updated[defaultWeekdayIndex()] = true;
    resetWeeklyDays.value = updated;
  }
};

const selectResetMode = (value: ConsumerResetTrigger) => {
  resetMode.value = value;
  if (value === 'weekly' && !resetWeeklyDays.value.some(Boolean)) {
    const updated = [...resetWeeklyDays.value];
    updated[defaultWeekdayIndex()] = true;
    resetWeeklyDays.value = updated;
  }
};

const toggleWeeklyDay = (index: number) => {
  const updated = [...resetWeeklyDays.value];
  updated[index] = !updated[index];
  resetWeeklyDays.value = updated;
};

const consumerUsageType = computed(() =>
  mqttStore.value.consumerUsageType(props.consumerId),
);

/** Meter-only consumers cannot be controlled, so hide the mode controls. */
const showModeControls = computed(
  () =>
    consumerUsageType.value !== 'meter_only' &&
    consumerUsageType.value !== 'self_controlled',
);
</script>

<style scoped lang="scss">
.dialog-width {
  width: 24em;
  max-width: 90vw;
}
</style>
