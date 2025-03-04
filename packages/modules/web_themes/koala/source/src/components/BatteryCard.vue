<template>
  <q-card class="full-height card-width">
    <q-card-section>
      <div class="row text-h6 items-center text-bold justify-between">
        <div>
          <q-icon
            name="battery_full"
            size="sm"
            class="q-mr-sm"
            color="primary"
          />
          {{ cardTitle }}
        </div>
        <q-icon
          v-if="showSettings"
          name="settings"
          size="sm"
          @click="dialog?.open()"
        />
      </div>
      <div class="row q-mt-sm text-subtitle2 justify-between no-wrap">
        <div class="row">
          <q-icon
            :name="
              soc === undefined || soc === null
                ? 'battery_0_bar'
                : soc < 85
                  ? `battery_${Math.floor(soc / 15)}_bar`
                  : 'battery_full'
            "
            size="sm"
            color="primary"
            class="rotate90Clockwise q-mr-sm"
          />
          <div>SoC:</div>
          <div class="q-ml-sm">
            {{ soc === undefined || soc === null ? '___%' : soc + '%' }}
          </div>
        </div>
        <div class="row">
          <div>Leistung:</div>
          <div class="q-ml-sm">
            {{ power }}
          </div>
        </div>
      </div>
      <div v-if="showSettings" class="row q-mt-md text-subtitle2">
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
      <div class="row q-mt-sm text-subtitle2">
        <div>Geladen:</div>
        <div class="q-ml-sm">
          {{ dailyImportedEnergy }}
        </div>
      </div>
      <div class="row q-mt-sm text-subtitle2">
        <div>Entladen:</div>
        <div class="q-ml-sm">
          {{ dailyExportedEnergy }}
        </div>
      </div>
    </q-card-section>
  </q-card>
  <BatterySettingsDialog :battery-id="props.batteryId" ref="dialog" />
</template>

<script setup lang="ts">
import { computed, ref } from 'vue';
import { useMqttStore } from 'src/stores/mqtt-store';
import BatterySettingsDialog from './BatterySettingsDialog.vue';
import { useBatteryModes } from 'src/composables/useBatteryModes.ts';

const props = defineProps<{
  batteryId: number | undefined;
}>();

const singleBattery = computed(() => {
  return mqttStore.batteryIds.length === 1;
});

const showSettings = computed(() => {
  return props.batteryId === undefined || singleBattery.value;
});

const { batteryModes } = useBatteryModes();

const batteryMode = computed(() => {
  const mode = mqttStore.batteryMode();
  return batteryModes.find((m) => m.value === mode.value) || batteryModes[0];
});

const dialog = ref();

const mqttStore = useMqttStore();

const cardTitle = computed(() => {
  if (props.batteryId === undefined) {
    return 'Speicher Übersicht';
  }
  return mqttStore.batteryName(props.batteryId);
});

const soc = computed(() => {
  if (props.batteryId === undefined) {
    return mqttStore.batterySocTotal;
  }
  return mqttStore.batterySoc(props.batteryId);
});

const power = computed(() => {
  if (props.batteryId === undefined) {
    return mqttStore.batteryTotalPower('textValue') as string | '---';
  }
  return mqttStore.batteryPower(props.batteryId, 'textValue') as string | '---';
});

const dailyImportedEnergy = computed(() => {
  if (props.batteryId === undefined) {
    return mqttStore.batteryDailyImportedTotal('textValue') as string | '---';
  }
  return (
    (mqttStore.batteryDailyImported(props.batteryId, 'textValue') as string) ||
    '---'
  );
});

const dailyExportedEnergy = computed(() => {
  if (props.batteryId === undefined) {
    return mqttStore.batteryDailyExportedTotal('textValue') as string | '---';
  }
  return (
    (mqttStore.batteryDailyExported(props.batteryId, 'textValue') as string) ||
    '---'
  );
});
</script>

<style lang="scss" scoped>
.rotate90Clockwise {
  transform: rotate(90deg);
}
.card-width {
  min-width: 24em;
}
</style>
