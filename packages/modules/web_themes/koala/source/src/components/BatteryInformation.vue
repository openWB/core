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
          {{ batteryName }}
        </div>
        <q-icon
          v-if="singleBattery"
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
          <div class="q-ml-sm" :class="powerClass">
            {{
              power < 0
                ? '>> ' + powerAbsolute
                : power > 0
                  ? '<< ' + powerAbsolute
                  : powerAbsolute
            }}
          </div>
        </div>
      </div>
      <div v-if="singleBattery" class="row q-mt-md text-subtitle2">
        <div>Überschuss Modus:</div>
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
  <BatterySettingsDialog ref="dialog" />
</template>

<script setup lang="ts">
import { computed, ref } from 'vue';
import { useMqttStore } from 'src/stores/mqtt-store';
import BatterySettingsDialog from './BatterySettingsDialog.vue';
import { useBatteryModes } from 'src/composables/useBatteryModes.ts';

const props = defineProps<{
  batteryId: number;
}>();

const singleBattery = computed(() => {
  return mqttStore.batteryIds.length === 1;
});

const { batteryModes } = useBatteryModes();

const batteryMode = computed(() => {
  const mode = mqttStore.batteryMode();
  return batteryModes.find((m) => m.value === mode.value) || batteryModes[0];
});

const dialog = ref();

const mqttStore = useMqttStore();

const batteryName = computed(() => mqttStore.batteryName(props.batteryId));

const soc = computed(() => mqttStore.batterySoc(props.batteryId));

const power = computed(() => {
  const power = mqttStore.batteryPower(props.batteryId, 'value');
  return typeof power === 'number' ? power : 0;
});

const powerAbsolute = computed(() =>
  mqttStore.batteryPower(props.batteryId, 'absoluteTextValue'),
);

const powerClass = computed(() => {
  const value = power.value;
  return value < 0
    ? 'text-negative'
    : value > 0
      ? 'text-positive'
      : 'text-neutral';
});

const dailyImportedEnergy = computed(() =>
  mqttStore.batteryDailyImported(props.batteryId),
);

const dailyExportedEnergy = computed(() =>
  mqttStore.batteryDailyExported(props.batteryId),
);
</script>

<style lang="scss" scoped>
.rotate90Clockwise {
  transform: rotate(90deg);
}
.text-negative {
  color: $red;
}

.text-positive {
  color: $green;
}

.text-neutral {
  color: $orange;
}
.card-width {
  min-width: 24em;
}
</style>
