<template>
  <div class="container" ref="rootRef">
    <div class="centered-panel">
      <div class="scroll-container">
        <div
          class="flex justify-between text-subtitle1 text-weight-bold q-mb-xs"
          ref="titleRef"
        >
          <div v-if="currentPowerVisible">Aktuelle Leistung</div>
          <div>Tageswerte</div>
        </div>
        <!-- grid -->
        <q-expansion-item
          dense
          expand-separator
          v-model="gridExpanded"
          class="grid q-mb-xs card"
          header-class="cursor-pointer"
        >
          <template #header>
            <DailyTotalsRow
              :item="gridData"
              :rowHeight="rowHeight"
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
          :class="[item.id, 'q-mb-xs', 'card']"
          header-class="no-pointer"
        >
          <template #header>
            <DailyTotalsRow
              :item="item"
              :rowHeight="rowHeight"
              :componentNameVisible="componentNameVisible"
              :currentPowerVisible="currentPowerVisible"
              :socValueVisible="socValueVisible"
            >
              <template #right-label>
                <template
                  v-if="item.id === 'battery' || item.id === 'chargepoint'"
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
                    )
                  "
                >
                  {{ item.today.imported }}
                </div>
                <div
                  v-if="
                    ['battery', 'grid', 'pv', 'chargepoint'].includes(item.id)
                  "
                >
                  {{ item.today.exported }}
                </div>
              </template>
            </DailyTotalsRow>
          </template>
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
const gridExpanded = ref(false);

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

const rootRef = ref<HTMLElement | null>(null);
const titleRef = ref<HTMLElement | null>(null);
const rowHeight = ref(45); // default / fallback

const totalRowCount = computed(() => {
  let count = 0;
  count += 1; // grid header
  count += secondaryCounterData.value.length; // secondary counters (only when expanded)
  count += componentData.value.length; // all other components
  return count;
});

let slideElement: HTMLElement | null = null;
let slideObserver: ResizeObserver | null = null;

function getSlideElement(): HTMLElement | null {
  return rootRef.value?.closest('.q-carousel__slide') as HTMLElement | null;
}

const calculateRowHeight = () => {
  nextTick(() => {
    const slide = slideElement ?? getSlideElement();
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
    const ROW_MIN = 32;
    const ROW_MAX = 70;
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
  slideElement = getSlideElement();

  if (slideElement) {
    slideObserver = new ResizeObserver(calculateRowHeight);
    slideObserver.observe(slideElement);
  }

  window.addEventListener('resize', calculateRowHeight, { passive: true });
  calculateRowHeight();
});

onBeforeUnmount(() => {
  slideObserver?.disconnect();
  slideObserver = null;
  window.removeEventListener('resize', calculateRowHeight);
});

// Recompute when rows or grid expansion change
watch(
  () => ({
    rows: componentData.value.length + secondaryCounterData.value.length,
    expanded: gridExpanded.value,
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
  padding: 0px 0px !important;
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
.grid,
.counter {
  border-radius: 8px;
}
.grid {
  background: var(--q-grid-fill);
  border: 2px solid var(--q-grid-stroke);
}
.counter {
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
.icon {
  filter: brightness(0.4);
}
.rotate-180 {
  transform: rotate(180deg);
}
/* Dark mode overrides */
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
.body--dark .icon {
  filter: brightness(1);
}
</style>
