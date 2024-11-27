<template>
  <q-card class="full-height card-width">
    <q-card-section>
      <div class="row justify-between">
        <div class="row text-h6 items-center text-bold">
          <q-icon
            name="battery_full"
            size="sm"
            class="q-mr-sm"
            color="primary"
          />
          Speicher Übersicht
        </div>
        <q-icon name="settings" size="sm" @click="settingsVisible = true" />
      </div>
      <div class="row q-mt-sm text-subtitle2 justify-between no-wrap">
        <div class="row">
          <q-icon
            :name="
              soc === 0 || soc === undefined || soc === null
                ? 'battery_0_bar'
                : soc < 14
                  ? 'battery_1_bar'
                  : soc < 29
                    ? 'battery_2_bar'
                    : soc < 43
                      ? 'battery_3_bar'
                      : soc < 57
                        ? 'battery_4_bar'
                        : soc < 71
                          ? 'battery_5_bar'
                          : soc < 85
                            ? 'battery_6_bar'
                            : 'battery_full'
            "
            size="sm"
            color="primary"
            class="rotate90Clockwise q-mr-sm"
          />
          <div>SoC:</div>
          <div class="q-ml-sm">{{ soc }}%</div>
        </div>
        <div class="row">
          <div>Leistung (gesamt):</div>
          <div class="q-ml-sm" :class="totalPowerClass">
            {{
              totalPower < 0
                ? '>> ' + totalPowerAbsolute
                : totalPower > 0
                  ? '<< ' + totalPowerAbsolute
                  : totalPowerAbsolute
            }}
          </div>
        </div>
      </div>
      <div class="text-subtitle1 text-weight-bold q-mt-sm">Heute:</div>
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

  <q-dialog
    v-model="settingsVisible"
    :maximized="$q.screen.width < 385"
    :backdrop-filter="$q.screen.width < 385 ? '' : 'blur(4px)'"
  >
    <q-card style="min-width: 24em">
      <q-card-section>
        <div class="text-h6">Battery Einstellungen</div>
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
import { useMqttStore } from 'src/stores/mqtt-store';
import { useQuasar } from 'quasar';
import BatteryModeButtons from './BatteryModeButtons.vue';

const settingsVisible = ref<boolean>(false);

const mqttStore = useMqttStore();
const $q = useQuasar();

const soc = computed(() => mqttStore.batterySocTotal);

const dailyImportedEnergy = computed(() =>
  mqttStore.batteryDailyImportedTotal('textValue'),
);

const dailyExportedEnergy = computed(() =>
  mqttStore.batteryDailyExportedTotal('textValue'),
);

const totalPower = computed(() => {
  const power = mqttStore.batteryTotalPower('value');
  return typeof power === 'number' ? power : 0;
});

const totalPowerAbsolute = computed(() =>
  mqttStore.batteryTotalPower('absoluteTextValue'),
);

const totalPowerClass = computed(() => {
  const value = totalPower.value;
  return value < 0
    ? 'text-negative'
    : value > 0
      ? 'text-positive'
      : 'text-neutral';
});
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
