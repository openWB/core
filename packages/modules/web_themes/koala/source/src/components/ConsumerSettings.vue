<template>
  <q-dialog v-model="visible">
    <q-card class="dialog-width">
      <q-card-section class="row items-center no-wrap">
        <div class="text-h6 ellipsis">Einstellungen {{ name }}</div>
        <q-space />
        <q-btn icon="close" flat round dense v-close-popup />
      </q-card-section>

      <q-separator />

      <q-card-section>
        <div class="text-subtitle2">Betriebsmodus</div>
        <ConsumerModeButtons :consumer-id="props.consumerId" />
      </q-card-section>

      <q-separator inset />

      <q-card-section>
        <div class="text-subtitle2">Betriebsmodus umstellen</div>
        <q-btn-group spread class="q-mt-sm">
          <q-btn
            v-for="trigger in resetTriggers"
            :key="trigger.value"
            size="sm"
            :color="resetTrigger === trigger.value ? 'primary' : 'grey'"
            :label="trigger.label"
            @click="selectTrigger(trigger.value)"
          />
        </q-btn-group>

        <div v-if="resetTrigger === 'time'" class="row q-col-gutter-sm q-mt-sm">
          <q-input v-model="resetDate" type="date" label="Datum" class="col" />
          <q-input
            v-model="resetTimeOfDay"
            type="time"
            label="Uhrzeit"
            class="col"
          />
        </div>

        <template v-if="resetTrigger !== 'never'">
          <div class="text-subtitle2 q-mt-md">Zielmodus</div>
          <q-btn-group spread class="q-mt-sm">
            <q-btn
              v-for="mode in chargeModes"
              :key="mode.value"
              size="sm"
              :color="resetTargetMode === mode.value ? 'primary' : 'grey'"
              :label="mode.label"
              @click="resetTargetMode = mode.value"
            />
          </q-btn-group>
        </template>
      </q-card-section>

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

const resetTriggers: { value: ConsumerResetTrigger; label: string }[] = [
  { value: 'never', label: 'Nie' },
  { value: 'midnight', label: 'Mitternacht' },
  { value: 'time', label: 'Zeitpunkt' },
];

const resetTrigger = mqttStore.consumerResetTrigger(props.consumerId);
const resetTargetMode = mqttStore.consumerResetTargetMode(props.consumerId);
const resetTime = mqttStore.consumerResetTime(props.consumerId);

const pad = (part: number) => String(part).padStart(2, '0');

const writeResetTime = (dateStr: string, timeStr: string) => {
  if (!dateStr || !timeStr) return;
  const epoch = Math.floor(new Date(`${dateStr}T${timeStr}`).getTime() / 1000);
  if (Number.isNaN(epoch)) return;
  resetTime.value = epoch;
};

const resetDate = computed({
  get: () => {
    const date = resetTime.value ? new Date(resetTime.value * 1000) : new Date();
    return `${date.getFullYear()}-${pad(date.getMonth() + 1)}-${pad(date.getDate())}`;
  },
  set: (dateStr: string) => writeResetTime(dateStr, resetTimeOfDay.value),
});

const resetTimeOfDay = computed({
  get: () => {
    const date = resetTime.value ? new Date(resetTime.value * 1000) : new Date();
    return `${pad(date.getHours())}:${pad(date.getMinutes())}`;
  },
  set: (timeStr: string) => writeResetTime(resetDate.value, timeStr),
});

const selectTrigger = (value: ConsumerResetTrigger) => {
  resetTrigger.value = value;
  if (value === 'time' && resetTime.value == null) {
    resetTime.value = Math.floor(Date.now() / 1000);
  }
};
</script>

<style scoped lang="scss">
.dialog-width {
  width: 24em;
  max-width: 90vw;
}
</style>
