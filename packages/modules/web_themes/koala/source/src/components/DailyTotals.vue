<template>
  <div class="daily-root">
    <div class="daily-center">
      <div class="daily-scroll-wrapper">
        <div class="daily-scroll">
          <div
            class="flex justify-between text-subtitle1 text-weight-bold q-mb-xs"
          >
            <div v-if="currentPowerVisible">Aktuelle Leistung</div>
            <div>Tageswerte</div>
          </div>
          <q-expansion-item
            dense
            expand-separator
            v-model="gridExpanded"
            class="grid q-mb-xs"
            header-class="cursor-pointer"
          >
            <!-- grid header -->
            <template #header>
              <div class="row items-center full-width no-wrap">
                <img
                  :src="gridData.icon"
                  class="icon q-mr-sm"
                  :style="{ width: iconSize + 'px', height: iconSize + 'px' }"
                />
                <div
                  v-if="componentNameVisible"
                  class="text-weight-bold q-mr-sm"
                >
                  {{ gridData.title }}
                </div>
                <div
                  class="row items-center q-mr-sm"
                  v-if="currentPowerVisible"
                >
                  <q-icon
                    :name="
                      arrowDirection('grid').noCurrent
                        ? 'horizontal_rule'
                        : 'double_arrow'
                    "
                    :class="{ 'rotate-180': arrowDirection('grid').rotate180 }"
                  />
                  <span class="q-ml-xs">
                    {{ String(gridData.power).replace('-', '') }}
                  </span>
                </div>

                <div class="col"></div>

                <div class="text-right text-weight-bold">
                  <div>Bezug: {{ gridData.today.imported }}</div>
                  <div>Einspeisung: {{ gridData.today.exported }}</div>
                </div>
              </div>
            </template>
            <!-- secondary counters -->
            <div
              v-for="item in secondaryCounterData"
              :key="item.id"
              class="counter"
            >
              <div class="row items-center full-width no-wrap">
                <img
                  src="icons/owbCounter.svg"
                  class="icon q-mr-sm"
                  :style="{ width: iconSize + 'px', height: iconSize + 'px' }"
                />
                <div
                  v-if="componentNameVisible"
                  class="text-weight-bold q-mr-sm"
                >
                  {{ item.title }}
                </div>
                <div
                  class="row items-center q-mr-sm"
                  v-if="currentPowerVisible"
                >
                  <q-icon
                    :name="
                      arrowDirection(item.id).noCurrent
                        ? 'horizontal_rule'
                        : 'double_arrow'
                    "
                    :class="{
                      'rotate-180': arrowDirection(item.id).rotate180,
                    }"
                  />
                  <span class="q-ml-xs">
                    {{ String(item.power).replace('-', '') }}
                  </span>
                </div>

                <div class="col"></div>

                <div class="text-right text-weight-bold">
                  <div>Bezug: {{ item.today.imported }}</div>
                  <div>Einspeisung: {{ item.today.exported }}</div>
                </div>
              </div>
            </div>
          </q-expansion-item>

          <!-- all other components -->
          <q-card
            v-for="item in componentData"
            :key="item.id"
            class="q-card q-mb-xs"
            :class="item.id"
            flat
            bordered
          >
            <q-card-section class="row items-center full-width no-wrap">
              <img
                :src="item.icon"
                class="icon q-mr-sm"
                :style="{ width: iconSize + 'px', height: iconSize + 'px' }"
              />
              <div v-if="componentNameVisible" class="text-weight-bold q-mr-sm">
                {{ item.title }}
              </div>
              <div
                v-if="socValueVisible && item.id === 'battery'"
                class="q-mr-sm"
              >
                {{ item.soc }}%
              </div>
              <div class="row items-center q-mr-sm" v-if="currentPowerVisible">
                <q-icon
                  :name="
                    arrowDirection(item.id).noCurrent
                      ? 'horizontal_rule'
                      : 'double_arrow'
                  "
                  :class="{ 'rotate-180': arrowDirection(item.id).rotate180 }"
                />
                <span class="q-ml-xs">
                  {{ String(item.power).replace('-', '') }}
                </span>
              </div>
              <div class="col"></div>
              <div class="text-right text-weight-bold">
                <div v-if="item.id !== 'pv' && item.id !== 'house'">
                  Geladen:
                  {{ item.today.imported }}
                </div>
                <div v-if="item.id !== 'pv' && item.id !== 'house'">
                  Entladen:
                  {{ item.today.exported }}
                </div>
                <div v-if="item.id === 'pv'">
                  Ertrag:
                  {{ item.today.exported }}
                </div>
                <div v-if="item.id === 'house'">
                  Ertrag:
                  {{ item.today.imported }}
                </div>
              </div>
            </q-card-section>
          </q-card>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed, ref } from 'vue';
import { useQuasar } from 'quasar';
import { useMqttStore } from 'src/stores/mqtt-store';
import type { DailyTotalsItem } from 'src/components/models/daily-totals-model';

const $q = useQuasar();
const mqttStore = useMqttStore();

const gridExpanded = ref(false);
const iconSize = ref(28);

const componentNameVisible = computed(() => $q.screen.width >= 375);
const currentPowerVisible = computed(() => $q.screen.width >= 500);
const socValueVisible = computed(() => $q.screen.width >= 700);

const batteryConfigured = computed(() => mqttStore.batteryConfigured);
const pvConfigured = computed(() => mqttStore.getPvConfigured);
const chargePointConfigured = computed(
  () => mqttStore.chargePointIds.length > 0,
);
const secondaryCountersConfigured = computed(
  () => mqttStore.getSecondaryCounterIds.length > 0,
);

const gridData = computed((): DailyTotalsItem => {
  return {
    id: 'grid',
    title: 'Netz',
    icon: 'icons/owbGrid.svg',
    power: mqttStore.getCounterPower('textValue') as string,
    powerValue: mqttStore.getCounterPower('value') as number,
    today: {
      imported: mqttStore.counterDailyImported('textValue') as string,
      exported: mqttStore.counterDailyExported('textValue') as string,
    },
  };
});

const secondaryCounterData = computed((): DailyTotalsItem[] => {
  const counters: DailyTotalsItem[] = [];
  if (gridExpanded.value && secondaryCountersConfigured.value) {
    mqttStore.getSecondaryCounterIds.forEach((id) => {
      counters.push({
        id: `counter-${id}`,
        title: mqttStore.getComponentName(id),
        icon: 'icons/owbCounter.svg',
        power: mqttStore.getCounterPower('textValue', id) as string,
        powerValue: mqttStore.getCounterPower('value', id) as number,
        today: {
          imported: mqttStore.counterDailyImported('textValue', id) as string,
          exported: mqttStore.counterDailyExported('textValue', id) as string,
        },
      });
    });
  }
  return counters;
});

const componentData = computed((): DailyTotalsItem[] => {
  const components: DailyTotalsItem[] = [];

  if (batteryConfigured.value) {
    components.push({
      id: 'battery',
      title: 'Speicher',
      icon: 'icons/owbBattery.svg',
      soc: mqttStore.batterySocTotal as number,
      power: mqttStore.batteryTotalPower('textValue') as string,
      powerValue: mqttStore.batteryTotalPower('value') as number,
      today: {
        imported: mqttStore.batteryDailyImportedTotal('textValue') as string,
        exported: mqttStore.batteryDailyExportedTotal('textValue') as string,
      },
    });
  }

  if (pvConfigured.value) {
    components.push({
      id: 'pv',
      title: 'PV',
      icon: 'icons/owbPV.svg',
      power: mqttStore.getPvPower('textValue') as string,
      powerValue: mqttStore.getPvPower('value') as number,
      today: { exported: mqttStore.pvDailyExported('textValue') as string },
    });
  }

  components.push({
    id: 'house',
    title: 'Haus',
    icon: 'icons/owbHouse.svg',
    power: mqttStore.getHomePower('textValue') as string,
    powerValue: mqttStore.getHomePower('value') as number,
    today: { imported: mqttStore.homeDailyYield('textValue') as string },
  });

  if (chargePointConfigured.value) {
    components.push({
      id: 'chargepoint',
      title: 'Ladepunkte',
      icon: 'icons/owbChargePoint.svg',
      power: mqttStore.chargePointSumPower('textValue') as string,
      powerValue: mqttStore.chargePointSumPower('value') as number,
      today: {
        imported: mqttStore.chargePointDailyImported('textValue') as string,
        exported: mqttStore.chargePointDailyExported('textValue') as string,
      },
    });
  }

  return components;
});

const arrowDirection = (id: string) => {
  let value = 0;
  switch (id) {
    case 'grid':
      value = mqttStore.getCounterPower('value') as number;
      break;
    case 'battery':
      value = mqttStore.batteryTotalPower('value') as number;
      break;
    case 'pv':
      value = mqttStore.getPvPower('value') as number;
      break;
    case 'house':
      value = mqttStore.getHomePower('value') as number;
      break;
    case 'chargepoint':
      value = mqttStore.chargePointSumPower('value') as number;
      break;
    default:
      if (id.startsWith('counter-')) {
        const counterId = Number(id.replace('counter-', ''));
        value = mqttStore.getCounterPower('value', counterId) as number;
      }
  }
  const noCurrent = value === 0;
  let rotate180 = false;

  if (id === 'grid') {
    rotate180 = value < 0;
  } else if (id !== 'house') {
    rotate180 = value > 0;
  }

  return { noCurrent, rotate180 };
};
</script>

<style scoped>
/* fills the carousel slide */
.daily-root {
  height: 100%;
  display: flex;
  justify-content: center;
}
/* fixed-width column */
.daily-center {
  width: 100%;
  max-width: 600px;
  height: 100%;
  display: flex;
  flex-direction: column;
}
/* wrapper */
.daily-scroll-wrapper {
  flex: 1;
  display: flex;
  align-items: center;
  overflow: hidden; /* clips scroll div */
}
/* scrolling area */
.daily-scroll {
  width: 100%;
  max-height: 100%; /* allows scrolling when needed */
  overflow-y: auto;
}

/* Hide expansion item chevron */
:deep(.q-expansion-item__toggle-icon) {
  display: none !important;
}

/* make padding same as cards inside expansion header */
:deep(.q-expansion-item__container .q-item) {
  padding: 3px 8px !important;
}

/* Remove the padding inside q-item__section */
:deep(.q-item__section) {
  padding: 0 !important;
  margin: 0 !important;
}

/* Apply same padding to Q-card */
:deep(.q-card__section) {
  padding: 3px 8px !important;
  min-height: 48px;
}

.q-card {
  border-radius: 8px;
}

.grid {
  border-radius: 8px;
  background: var(--q-grid-fill);
  border: 2px solid var(--q-grid-stroke);
}

.counter {
  border-radius: 8px;
  padding: 3px 8px;
  background: var(--q-secondary-counter-fill);
  border: 2px solid var(--q-secondary-counter-stroke);
}
.battery {
  background: var(--q-battery-fill);
  border: 2px solid var(--q-battery-stroke);
}
.pv {
  background: var(--q-pv-fill);
  border: 2px solid var(--q-pv-stroke);
}
.house {
  background: var(--q-home-fill);
  border: 2px solid var(--q-home-stroke);
}
.chargepoint {
  background: var(--q-charge-point-fill);
  border: 2px solid var(--q-charge-point-stroke);
}

.body--dark .grid {
  background: #a13a41 !important;
  border: 2px solid #da959a;
}
.body--dark .battery {
  background: #b97a1f;
  border: 2px solid #e7c08a;
}
.body--dark .pv {
  background: #27623a;
}
.body--dark .house {
  background: #6e6e6e;
}
.body--dark .chargepoint {
  background: #254a8c;
}

.icon {
  filter: brightness(0.4);
}
.body--dark .icon {
  filter: brightness(1);
}

.rotate-180 {
  transform: rotate(180deg);
}
</style>
