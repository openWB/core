<template>
  <div class="container" ref="rootRef">
    <div class="centered-panel">
      <div class="scroll-container narrow-scrollbar">
        <div
          class="flex justify-between text-subtitle1 text-weight-bold q-mb-xs"
          ref="titleRef"
        >
          <div v-if="currentPowerVisible">Aktuelle Leistung</div>
          <div>Tageswerte</div>
        </div>
        <!-- grid -->
        <q-expansion-item
          v-if="showGrid"
          dense
          expand-separator
          v-model="expanded.grid"
          class="grid card"
          :header-class="
            secondaryCountersConfigured ? 'cursor-pointer' : 'no-pointer'
          "
        >
          <template #header>
            <DailyTotalsRow
              :item="gridData"
              :rowHeight="rowHeight"
              :rowExpanded="expanded.grid"
              :secondaryComponentsConfigured="secondaryCountersConfigured"
              :componentNameVisible="componentNameVisible"
              :currentPowerVisible="currentPowerVisible"
              :socValueVisible="socValueVisible"
            />
          </template>
          <!-- Secondary Counters -->
          <div
            v-for="item in secondaryCounterData"
            :key="item.id"
            class="counter"
          >
            <DailyTotalsRow
              :item="item"
              :rowHeight="rowHeight"
              :componentNameVisible="componentNameVisible"
              :currentPowerVisible="currentPowerVisible"
              :socValueVisible="socValueVisible"
            />
          </div>
        </q-expansion-item>
        <!-- all other components -->
        <q-expansion-item
          v-for="item in componentData"
          :key="item.id"
          dense
          expand-separator
          v-model="expanded[item.id]"
          :class="[item.id, 'card']"
          :header-class="
            item.id === 'chargepoint' ? 'cursor-pointer' : 'no-pointer'
          "
        >
          <template #header>
            <DailyTotalsRow
              :item="item"
              :rowHeight="rowHeight"
              :rowExpanded="expanded[item.id]"
              :secondaryComponentsConfigured="
                item.id === 'chargepoint'
                  ? individualChargePointData.length > 0
                  : false
              "
              :componentNameVisible="componentNameVisible"
              :currentPowerVisible="currentPowerVisible"
              :socValueVisible="socValueVisible"
            >
              <template #right-label>
                <template
                  v-if="
                    ['battery', 'chargepoint'].includes(item.id) &&
                    item.today !== undefined
                  "
                >
                  <div>Geladen:</div>
                  <div>Entladen:</div>
                </template>
                <template v-else-if="item.id === 'pv'">
                  <div>Ertrag:</div>
                </template>
                <template v-else-if="item.id === 'house'">
                  <div>Verbrauch:</div>
                </template>
              </template>
              <template #right-value>
                <div
                  v-if="
                    ['battery', 'grid', 'house', 'chargepoint'].includes(
                      item.id,
                    ) && item.today !== undefined
                  "
                >
                  {{ item.today.imported }}
                </div>
                <div
                  v-if="
                    ['battery', 'grid', 'pv', 'chargepoint'].includes(
                      item.id,
                    ) && item.today !== undefined
                  "
                >
                  {{ item.today.exported }}
                </div>
              </template>
            </DailyTotalsRow>
          </template>
          <div v-if="item.id === 'chargepoint'">
            <DailyTotalsRow
              v-for="chargePointData in individualChargePointData"
              :key="chargePointData.id"
              :item="chargePointData"
              :rowHeight="rowHeight"
              :componentNameVisible="componentNameVisible"
              :currentPowerVisible="currentPowerVisible"
              :socValueVisible="socValueVisible"
            >
              <template #right-label>
                <template v-if="chargePointData.today !== undefined">
                  <div>Geladen:</div>
                  <div>Entladen:</div>
                </template>
              </template>
              <template #right-value>
                <div v-if="chargePointData.today !== undefined">
                  {{ chargePointData.today.imported }}
                </div>
                <div v-if="chargePointData.today !== undefined">
                  {{ chargePointData.today.exported }}
                </div>
              </template>
            </DailyTotalsRow>
          </div>
        </q-expansion-item>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import {
  computed,
  ref,
  onMounted,
  onBeforeUnmount,
  nextTick,
  watch,
} from 'vue';
import { useQuasar } from 'quasar';
import { useMqttStore } from 'src/stores/mqtt-store';
import DailyTotalsRow from './DailyTotalsRow.vue';
import type { DailyTotalsItem } from 'src/components/models/daily-totals-model';

const $q = useQuasar();
const mqttStore = useMqttStore();
const gridPower = computed(() => mqttStore.getCounterPower('value'));
const showGrid = computed(
  () => gridPower.value !== undefined || secondaryCountersConfigured.value,
);
const expanded = ref({
  grid: false,
  chargepoint: false,
  battery: false,
  pv: false,
});

const componentNameVisible = computed(() => $q.screen.width >= 375);
const currentPowerVisible = computed(() => $q.screen.width >= 500);
const socValueVisible = computed(() => $q.screen.width >= 700);

const showHomePower = computed(() => {
  return mqttStore.getHomePower('value') !== undefined;
});
const batteryConfigured = computed(() => mqttStore.batteryConfigured);
const pvConfigured = computed(() => mqttStore.getPvConfigured);
const chargePointSumPowerAvailable = computed(
  () => mqttStore.chargePointSumPower('value') !== undefined,
);
const chargePointConfigured = computed(
  () => mqttStore.chargePointIds.length > 0,
);
const secondaryCountersConfigured = computed(
  () => secondaryCounterData.value.length > 0,
);

const gridData = computed((): DailyTotalsItem => {
  let data: DailyTotalsItem = {
    id: 'grid',
    title: 'Zähler',
    icon: 'icons/owbCounter.svg',
  };
  if (gridPower.value !== undefined) {
    data = {
      ...data,
      title: 'Netz',
      icon: 'icons/owbGrid.svg',
      power: mqttStore.getCounterPower('textValue') as string,
      powerValue: mqttStore.getCounterPower('value') as number,
      today: {
        imported: mqttStore.counterDailyImported('textValue') as string,
        exported: mqttStore.counterDailyExported('textValue') as string,
      },
    };
  }
  return data;
});

const secondaryCounterData = computed((): DailyTotalsItem[] => {
  const counters: DailyTotalsItem[] = [];
  mqttStore.getSecondaryCounterIds.forEach((id) => {
    const name = mqttStore.getComponentName(id);
    if (name !== undefined) {
      counters.push({
        id: `counter-${id}`,
        title: name,
        icon: 'icons/owbCounter.svg',
        power: mqttStore.getCounterPower('textValue', id) as string,
        powerValue: mqttStore.getCounterPower('value', id) as number,
        today: {
          imported: mqttStore.counterDailyImported('textValue', id) as string,
          exported: mqttStore.counterDailyExported('textValue', id) as string,
        },
      });
    }
  });
  return counters;
});

const individualChargePointData = computed((): DailyTotalsItem[] => {
  const chargePoints: DailyTotalsItem[] = [];
  mqttStore.chargePointIds.forEach((id) => {
    const name = mqttStore.chargePointName(id);
    if (name !== undefined) {
      chargePoints.push({
        id: `chargepoint-${id}`,
        title: name,
        icon: 'icons/owbChargePoint.svg',
        power: mqttStore.chargePointPower(id, 'textValue') as string,
        powerValue: mqttStore.chargePointPower(id, 'value') as number,
        today: {
          imported: mqttStore.chargePointDailyImported(
            'textValue',
            id,
          ) as string,
          exported: mqttStore.chargePointDailyExported(
            'textValue',
            id,
          ) as string,
        },
      });
    }
  });
  return chargePoints;
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

  if (showHomePower.value) {
    components.push({
      id: 'house',
      title: 'Haus',
      icon: 'icons/owbHouse.svg',
      power: mqttStore.getHomePower('textValue') as string,
      powerValue: mqttStore.getHomePower('value') as number,
      today: { imported: mqttStore.homeDailyYield('textValue') as string },
    });
  }

  if (chargePointConfigured.value || chargePointSumPowerAvailable.value) {
    let item: DailyTotalsItem = {
      id: 'chargepoint',
      title: 'Ladepunkte',
      icon: 'icons/owbChargePoint.svg',
    };
    if (chargePointSumPowerAvailable.value) {
      item = {
        ...item,
        power: mqttStore.chargePointSumPower('textValue') as string,
        powerValue: mqttStore.chargePointSumPower('value') as number,
        today: {
          imported: mqttStore.chargePointDailyImported('textValue') as string,
          exported: mqttStore.chargePointDailyExported('textValue') as string,
        },
      };
    }
    components.push(item);
  }
  return components;
});

const rootRef = ref<HTMLElement | null>(null);
const titleRef = ref<HTMLElement | null>(null);
const rowHeight = ref(45); // default / fallback

const totalRowCount = computed(() => {
  // grid header + secondary counters (only when expanded) + other components
  return 1 + secondaryCounterData.value.length + componentData.value.length;
});

const slideObserver = ref<ResizeObserver | null>(null);
const slideElement = computed<HTMLElement | null>(() => {
  return rootRef.value?.closest('.q-carousel__slide') as HTMLElement | null;
});

const calculateRowHeight = () => {
  nextTick(() => {
    const slide = slideElement.value;
    if (!slide) return;
    const style = window.getComputedStyle(slide);
    const paddings =
      parseFloat(style.paddingTop || '0') +
      parseFloat(style.paddingBottom || '0');
    const totalHeight = slide.clientHeight - paddings;
    const titleHeight = titleRef.value?.offsetHeight ?? 0;
    // small vertical gaps between rows + some safety padding
    const verticalGaps = (totalRowCount.value - 1) * 4;
    const safetyPadding = 40;
    const availableHeight = Math.max(
      0,
      totalHeight - titleHeight - verticalGaps - safetyPadding,
    );
    const ROW_MIN = 42;
    const ROW_MAX = 75;
    if (totalRowCount.value <= 0) {
      rowHeight.value = ROW_MIN;
      return;
    }
    rowHeight.value = Math.max(
      ROW_MIN,
      Math.min(ROW_MAX, Math.floor(availableHeight / totalRowCount.value)),
    );
  });
};

onMounted(() => {
  if (slideElement.value) {
    slideObserver.value = new ResizeObserver(calculateRowHeight);
    slideObserver.value.observe(slideElement.value);
  }

  window.addEventListener('resize', calculateRowHeight, { passive: true });
  calculateRowHeight();
});

onBeforeUnmount(() => {
  slideObserver.value?.disconnect();
  slideObserver.value = null;
  window.removeEventListener('resize', calculateRowHeight);
});

// Recompute when rows or grid expansion change
watch(
  () => ({
    rows: componentData.value.length + secondaryCounterData.value.length,
    expanded: expanded.value.grid,
  }),
  () => calculateRowHeight(),
);
</script>

<style scoped>
.container {
  height: 100%;
  display: flex;
  justify-content: center;
}
.centered-panel {
  width: 100%;
  max-width: 600px;
  height: 100%;
  display: flex;
  align-items: center;
  overflow: hidden; /* clip scroll area */
}
.scroll-container {
  width: 100%;
  max-height: 100%;
  overflow-y: auto; /* show scrollbar when needed */
}
/* Hide expansion item chevron */
:deep(.q-expansion-item__toggle-icon) {
  display: none !important;
}
/* Remove the padding inside expansion header */
:deep(.q-expansion-item__container .q-item) {
  padding: 0 0 !important;
}
/* Remove the padding inside q-item__section */
:deep(.q-item__section) {
  padding: 0 !important;
  margin: 0 !important;
}
/* headers that should NOT look clickable */
:deep(.no-pointer) {
  cursor: default !important;
}
/* Expansion item: override any clickable helper classes- prevent cursor: pointer */
:deep(.no-pointer.q-item--clickable),
:deep(.no-pointer.q-link),
:deep(.no-pointer.cursor-pointer) {
  cursor: default !important;
  pointer-events: none;
}
.card,
.grid {
  border-radius: 0.5rem;
  margin-bottom: 0.125rem;
}
.grid {
  background: var(--q-grid-fill);
  border: 0.125rem solid var(--q-grid-stroke);
}
.counter {
  background: var(--q-secondary-counter-fill);
  border-top: 0.125rem solid var(--q-secondary-counter-stroke);
  border-left: 0;
  border-right: 0;
  border-bottom: 0;
}
.battery {
  background: var(--q-battery-fill);
  border: 0.125rem solid var(--q-battery-stroke);
}
.pv {
  background: var(--q-pv-fill);
  border: 0.125rem solid var(--q-pv-stroke);
}
.house {
  background: var(--q-home-fill);
  border: 0.125rem solid var(--q-home-stroke);
}
.chargepoint {
  background: var(--q-charge-point-fill);
  border: 0.125rem solid var(--q-charge-point-stroke);
}
.rotate-180 {
  transform: rotate(180deg);
}
/* Dark mode overrides */
.body--dark .grid {
  background: var(--q-dark-daily-totals-grid-fill);
  border: 0.125rem solid var(--q-dark-daily-totals-grid-stroke);
}
.body--dark .battery {
  background: var(--q-dark-daily-totals-battery-fill);
  border: 0.125rem solid var(--q-dark-daily-totals-battery-stroke);
}
.body--dark .pv {
  background: var(--q-dark-daily-totals-pv-fill);
}
.body--dark .house {
  background: var(--q-dark-daily-totals-house-fill);
}
.body--dark .chargepoint {
  background: var(--q-dark-daily-totals-chargepoint-fill);
}
</style>
