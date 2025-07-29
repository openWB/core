<template>
  <q-card
    ref="cardRef"
    class="full-height card-width"
    :class="{ 'battery-sum': props.batteryId === -1 }"
  >
    <q-card-section>
      <div class="row text-h6 items-center text-bold justify-between">
        {{ cardTitle }}
        <q-icon
          class="cursor-pointer"
          v-if="showSettings"
          name="settings"
          size="sm"
          @click="dialog?.open()"
        />
      </div>
      <div class="row q-mt-sm text-subtitle2 justify-between full-width">
        <div>Leistung:</div>
        <div class="q-ml-sm">
          {{ power }}
        </div>
      </div>
      <div
        v-if="showSettings"
        class="row q-mt-md justify-between text-subtitle2"
      >
        <div>Laden mit Überschuss:</div>
        <div class="q-ml-sm row items-center">
          <q-icon
            :name="batteryMode.icon"
            size="sm"
            class="q-mr-sm"
            color="primary"
          />
          {{ batteryMode.label }}
        </div>
      </div>
      <div class="text-subtitle1 text-weight-bold q-mt-md">Heute:</div>
      <div class="row q-mt-sm text-subtitle2 justify-between full-width">
        <div>Geladen:</div>
        <div class="q-ml-sm">
          {{ dailyImportedEnergy }}
        </div>
      </div>
      <div class="row q-mt-sm text-subtitle2 justify-between full-width">
        <div>Entladen:</div>
        <div class="q-ml-sm">
          {{ dailyExportedEnergy }}
        </div>
      </div>
      <SliderDouble
        class="q-mt-sm"
        :current-value="soc"
        :readonly="true"
        limit-mode="none"
      />
    </q-card-section>
  </q-card>
  <BatterySettingsDialog :battery-id="props.batteryId" ref="dialog" />
</template>

<script setup lang="ts">
import { computed, ref, onMounted, inject } from 'vue';
import { useMqttStore } from 'src/stores/mqtt-store';
import BatterySettingsDialog from './BatterySettingsDialog.vue';
import { useBatteryModes } from 'src/composables/useBatteryModes.ts';
import SliderDouble from './SliderDouble.vue';

const cardRef = ref<{ $el: HTMLElement } | null>(null);
const setCardWidth = inject<((width: number | undefined) => void) | undefined>(
  'setCardWidth',
  undefined,
);

const props = defineProps<{
  batteryId: number;
}>();

const singleBattery = computed(() => {
  return mqttStore.batteryIds.length === 1;
});

const showSettings = computed(() => {
  return isOverview.value || singleBattery.value;
});

const { batteryModes } = useBatteryModes();

const isOverview = computed(() => {
  return props.batteryId === -1;
});

const batteryMode = computed(() => {
  const mode = mqttStore.batteryMode();
  return batteryModes.find((m) => m.value === mode.value) || batteryModes[0];
});

const dialog = ref();

const mqttStore = useMqttStore();

const cardTitle = computed(() => {
  if (isOverview.value) {
    return 'Speicher Übersicht';
  }
  return mqttStore.batteryName(props.batteryId);
});

const soc = computed(() => {
  if (isOverview.value) {
    return mqttStore.batterySocTotal;
  }
  return mqttStore.batterySoc(props.batteryId);
});

const power = computed(() => {
  if (isOverview.value) {
    return mqttStore.batteryTotalPower('textValue') as string | '---';
  }
  return mqttStore.batteryPower(props.batteryId, 'textValue') as string | '---';
});

const dailyImportedEnergy = computed(() => {
  if (isOverview.value) {
    return mqttStore.batteryDailyImportedTotal('textValue') as string | '---';
  }
  return (
    (mqttStore.batteryDailyImported(props.batteryId, 'textValue') as string) ||
    '---'
  );
});

const dailyExportedEnergy = computed(() => {
  if (isOverview.value) {
    return mqttStore.batteryDailyExportedTotal('textValue') as string | '---';
  }
  return (
    (mqttStore.batteryDailyExported(props.batteryId, 'textValue') as string) ||
    '---'
  );
});

onMounted(() => {
  const cardWidth = cardRef.value?.$el.clientWidth;
  setCardWidth?.(cardWidth);
});
</script>

<style scoped>
.card-width {
  width: 22em;
}
</style>
