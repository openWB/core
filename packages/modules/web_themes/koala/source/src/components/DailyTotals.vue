<template>
  <div class="q-pa-md flex justify-center items-center container">
    <div class="full-width banner-container">
      <div class="flex justify-between text-subtitle1 text-weight-bold">
        <div v-if="!$q.platform.is.mobile">Aktuelle Leistung</div>
        <div>Tageswerte</div>
      </div>
      <q-banner
        v-for="item in dailyTotalsItems"
        :key="item.id"
        class="full-width banner"
        rounded
        dense
        :style="{ backgroundColor: item.backgroundColor }"
      >
        <div class="row no-wrap items-center justify-between">
          <!-- Banner left side: icon + title + arrow/dash + power value-->
          <div class="row no-wrap items-center" :class="screenWidthMd ? 'text-caption' : 'text-body2'">
            <img
              :src="item.icon"
              :alt="item.title"
              class="icon q-mr-sm"
              :style="{ width: iconSize + 'px', height: iconSize + 'px' }"
            />
            <div v-if="!screenWidthXs" :class="screenWidthMd ? 'spacer-component-label' : 'spacer-component-label-soc'">
              <span class="text-weight-bold">{{ item.title }}</span>
              <span v-if="item.id === 'battery' && !screenWidthMd">&nbsp;-&nbsp;{{ item.soc }}%</span>
            </div>
            <div v-if="!screenWidthSm" class="row items-center">
              <q-icon
                :name="
                  item.id === 'house'
                    ? 'horizontal_rule'
                    : arrowDirection(item.id).noCurrent
                      ? 'horizontal_rule'
                      : 'double_arrow'
                "
                :class="{ 'rotate-180': arrowDirection(item.id).rotate180 }"
                class="q-mx-sm"
              />
              <div class="spacer-power-value">
                <span>
                  {{ String(item.power).replace('-', '') }}
                </span>
              </div>
            </div>
          </div>
          <!-- Banner right side: energy description  + energy values -->
          <div class="row no-wrap" :class="screenWidthMd ? 'text-caption' : 'text-body2'">
            <!-- Battery -->
            <div v-if="item.id === 'battery'" class="row">
              <div class="column text-right">
                <span class="text-weight-bold">Geladen:</span>
                <span class="text-weight-bold">Entladen:</span>
              </div>
              <div class="column text-right q-ml-sm spacer-energy-value">
                <span>{{ item.today.charged }}</span>
                <span>{{ item.today.discharged }}</span>
              </div>
            </div>
            <!-- Grid -->
            <div v-else-if="item.id === 'grid'" class="row">
              <div class="column text-right">
                <span class="text-weight-bold">Bezug:</span>
                <span class="text-weight-bold">Einspeisung:</span>
              </div>
              <div class="column text-right q-ml-sm spacer-energy-value">
                <span>{{ item.today.imported }}</span>
                <span>{{ item.today.exported }}</span>
              </div>
            </div>
            <!-- PV -->
            <div v-else-if="item.id === 'pv'" class="row text-right">
              <span class="q-mr-sm text-weight-bold">Ertrag:</span>
              <span class="spacer-energy-value">{{ item.today.yield }}</span>
            </div>
            <!-- House -->
            <div
              v-else-if="item.id === 'house'"
              class="row text-right"
            >
              <span class="q-mr-sm text-weight-bold">Energie:</span>
              <span class="spacer-energy-value">{{ item.today.energy }}</span>
            </div>
            <!-- Chargepoints -->
            <div
              v-else-if="item.id === 'chargepoint'"
              class="row text-right"
            >
              <span class="q-mr-sm text-weight-bold">Geladen:</span>
              <span class="spacer-energy-value">{{ item.today.charged }}</span>
            </div>
          </div>
        </div>
      </q-banner>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue';
import { useMqttStore } from 'src/stores/mqtt-store';
import type { DailyTotalsItem } from 'src/components/models/daily-totals-model';
import { useQuasar } from 'quasar';

const $q = useQuasar();

const screenWidthXs = computed(() => $q.screen.width <= 380);
const screenWidthSm = computed(() => $q.screen.width <= 500);
const screenWidthMd = computed(() => $q.screen.width <= 700);

const iconSize = computed(() => {
  if (screenWidthSm.value) return 24;
  return 28;
});

const mqttStore = useMqttStore();

// Battery
const batteryPower = computed(() => ({
  value: mqttStore.batteryTotalPower('value') as number,
  textValue: mqttStore.batteryTotalPower('textValue') as string,
}));
const batterySoC = computed(() => mqttStore.batterySocTotal);
const batteryDailyExported = computed(
  () => mqttStore.batteryDailyExportedTotal('textValue') as string,
);
const batteryDailyImported = computed(
  () => mqttStore.batteryDailyImportedTotal('textValue') as string,
);

// PV
const pvPower = computed(() => ({
  value: mqttStore.getPvPower('value') as number,
  textValue: mqttStore.getPvPower('textValue') as string,
}));
const pvEnergyToday = computed(
  () => mqttStore.pvDailyExported('textValue') as string,
);

// Grid
const gridPower = computed(() => ({
  value: mqttStore.getGridPower('value') as number,
  textValue: mqttStore.getGridPower('textValue') as string,
}));
const gridEnergyToday = computed(
  () => mqttStore.gridDailyImported('textValue') as string,
);
const gridEnergyExportedToday = computed(
  () => mqttStore.gridDailyExported('textValue') as string,
);

// Home
const homePower = computed(() => ({
  value: mqttStore.getHomePower('value') as number,
  textValue: mqttStore.getHomePower('textValue') as string,
}));
const homeDailyYield = computed(
  () => mqttStore.homeDailyYield('textValue') as string,
);

// ChargePoints
const chargePointPower = computed(() => ({
  value: mqttStore.chargePointSumPower('value') as number,
  textValue: mqttStore.chargePointSumPower('textValue') as string,
}));
const chargePointDailyImported = computed(
  () => mqttStore.chargePointDailyImported('textValue') as string,
);

const dailyTotalsItems = computed((): DailyTotalsItem[] => [
  {
    id: 'grid',
    title: 'Netz',
    icon: 'icons/owbGrid.svg',
    power: gridPower.value.textValue,
    powerValue: gridPower.value.value,
    today: {
      imported: gridEnergyToday.value,
      exported: gridEnergyExportedToday.value,
    },
    backgroundColor: 'rgb(213,187,192)',
  },
  {
    id: 'battery',
    title: 'Speicher',
    icon: 'icons/owbBattery.svg',
    soc: batterySoC.value,
    power: batteryPower.value.textValue,
    powerValue: batteryPower.value.value,
    today: {
      charged: batteryDailyImported.value,
      discharged: batteryDailyExported.value,
    },
    backgroundColor: 'rgb(199,163,136)',
  },
  {
    id: 'pv',
    title: 'PV',
    icon: 'icons/owbPV.svg',
    power: pvPower.value.textValue,
    powerValue: pvPower.value.value,
    today: { yield: pvEnergyToday.value },
    backgroundColor: 'rgb(179,204,188)',
  },
  {
    id: 'house',
    title: 'Haus',
    icon: 'icons/owbHouse.svg',
    power: homePower.value.textValue,
    powerValue: homePower.value.value,
    today: { energy: homeDailyYield.value },
    backgroundColor: 'rgb(186,186,191)',
  },
  {
    id: 'chargepoint',
    title: 'Ladepunkte',
    icon: 'icons/owbChargePoint.svg',
    power: chargePointPower.value.textValue,
    powerValue: chargePointPower.value.value,
    today: { charged: chargePointDailyImported.value },
    backgroundColor: 'rgb(177,192,214)',
  },
]);

const getArrowDirection = computed(() =>
  dailyTotalsItems.value.map((item) => {
    let rotate = false;
    let noCurrent = false;
    if (item.powerValue === 0) noCurrent = true;
    if (item.id === 'grid') {
      rotate = Number(item.powerValue) < 0;
    } else {
      rotate = Number(item.powerValue) > 0;
    }
    return { id: item.id, rotate180: rotate, noCurrent };
  }),
);

const arrowDirection = (itemId: string) =>
  getArrowDirection.value.find((c) => c.id === itemId) ??
  ({ rotate180: false, noCurrent: false } as const);
</script>

<style scoped>
.container {
  min-height: 100%;
  overflow-y: auto;
}

.banner-container {
  max-width: 600px;
  height: 100%;
}

.banner {
  border-radius: 8px;
  padding: 3px 8px;
  margin-bottom: 4px;
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.15);
}

.icon {
  width: 28px;
  height: 28px;
  filter: brightness(0.4);
}
.body--dark .icon {
  filter: brightness(1);
}

.rotate-180 {
  transform: rotate(180deg);
}

.spacer-energy-value {
  min-width: 10ch;
}

.spacer-component-label {
  min-width: 11ch;
}

.spacer-component-label-soc {
  min-width: 14ch;
}

.spacer-power-value {
  min-width: 8ch;
  text-align: right;
}
</style>
