<template>
  <q-dialog v-model="visible">
    <q-card class="dialog-width">
      <q-card-section class="row items-center no-wrap">
        <div class="text-h6 ellipsis">Einstellungen {{ name }}</div>
        <q-space />
        <q-btn icon="close" flat round dense v-close-popup />
      </q-card-section>

      <template v-if="showModeControls">
        <q-separator />

        <q-card-section>
          <div class="text-subtitle2">Betriebsmodus</div>
          <ConsumerModeButtons :consumer-id="props.consumerId" />
        </q-card-section>

        <q-separator inset />

        <q-card-section>
          <div class="text-subtitle2">Betriebsmodus umstellen</div>
          <q-btn-group spread outline class="q-mt-sm">
            <q-btn
              size="sm"
              :outline="resetEnabled"
              :color="!resetEnabled ? 'negative' : 'grey'"
              label="Nein"
              @click="setResetEnabled(false)"
            />
            <q-btn
              size="sm"
              :outline="!resetEnabled"
              :color="resetEnabled ? 'positive' : 'grey'"
              label="Ja"
              @click="setResetEnabled(true)"
            />
          </q-btn-group>

          <template v-if="resetEnabled">
            <q-input
              v-model="resetTime"
              type="time"
              label="Uhrzeit"
              class="q-mt-sm"
            />

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
              class="row q-col-gutter-xs q-mt-sm"
            >
              <div
                v-for="(day, index) in weekDays"
                :key="day"
                class="col"
              >
                <q-btn
                  no-caps
                  size="sm"
                  class="full-width"
                  :outline="!resetWeeklyDays[index]"
                  :color="resetWeeklyDays[index] ? 'primary' : 'grey'"
                  :label="day"
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
      <q-card-actions align="right">
        <q-btn
          flat
          dense
          no-caps
          icon="tune"
          label="Geräte-Einstellungen"
          type="a"
          href="/openWB/web/settings/#/ConsumerConfiguration"
          :title="`Geräte-Einstellungen ${name ?? ''}`"
        />
      </q-card-actions>
    </q-card>
  </q-dialog>
</template>

<script setup lang="ts">
import { computed } from 'vue';
import { useMqttStore } from 'src/stores/mqtt-store';
import { useChargeModes } from 'src/composables/useChargeModes';
import type { ConsumerResetTrigger } from 'src/stores/mqtt-store-model';
import ConsumerModeButtons from './ConsumerModeButtons.vue';

const props = defineProps<{
  consumerId: number;
  modelValue: boolean;
}>();

const emit = defineEmits<{
  'update:modelValue': [value: boolean];
}>();

const mqttStore = useMqttStore();
const { chargeModes } = useChargeModes();

const name = computed(() => mqttStore.consumerName(props.consumerId));

const visible = computed({
  get: () => props.modelValue,
  set: (value) => emit('update:modelValue', value),
});

const resetModes: { value: ConsumerResetTrigger; label: string }[] = [
  { value: 'once', label: 'Einmalig' },
  { value: 'daily', label: 'Täglich' },
  { value: 'weekly', label: 'Wöchentlich' },
];

const resetEnabled = mqttStore.consumerResetEnabled(props.consumerId);
const resetMode = mqttStore.consumerResetTrigger(props.consumerId);
const resetTargetMode = mqttStore.consumerResetTargetMode(props.consumerId);
const resetTime = mqttStore.consumerResetTime(props.consumerId);
const resetOnceDate = mqttStore.consumerResetOnceDate(props.consumerId);
const resetWeeklyDays = mqttStore.consumerResetWeeklyDays(props.consumerId);
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
  mqttStore.consumerUsageType(props.consumerId),
);

/** Meter-only consumers cannot be controlled, so hide the mode controls. */
const showModeControls = computed(
  () => consumerUsageType.value !== 'meter_only' && consumerUsageType.value !== 'self_controlled',
);
</script>

<style scoped lang="scss">
.dialog-width {
  width: 24em;
  max-width: 90vw;
}
</style>
