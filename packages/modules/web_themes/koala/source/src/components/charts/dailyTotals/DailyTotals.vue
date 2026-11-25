<template>
  <div
    class="container"
    :class="{ 'totals-desktop': props.desktop }"
    ref="rootRef"
  >
    <div class="centered-panel">
      <div class="scroll-container narrow-scrollbar">
        <div
          v-if="!props.desktop"
          class="flex justify-between text-subtitle1 text-weight-bold q-mb-xs"
          ref="titleRef"
        >
          <div v-if="currentPowerVisible && !props.desktop">
            Aktuelle Leistung
          </div>
          <div>
            {{
              props.desktop ? 'Aktuelle Leistung und Tageswerte' : 'Tageswerte'
            }}
          </div>
        </div>
        <!-- grid -->
        <q-expansion-item
          v-if="showGrid"
          dense
          :expand-separator="!props.desktop"
          v-model="expanded.grid"
          class="grid card"
          :header-class="
            props.desktop || secondaryComponentsConfigured('counter')
              ? 'cursor-pointer'
              : 'no-pointer'
          "
        >
          <template #header>
            <DailyTotalsRow
              :item="gridData"
              :rowHeight="rowHeight"
              :rowExpanded="expanded.grid"
              :hideDailyTotals="props.desktop && !expanded.grid"
              :secondaryComponentsConfigured="
                props.desktop || secondaryComponentsConfigured('counter')
              "
              :componentNameVisible="componentNameVisible"
              :currentPowerVisible="currentPowerVisible"
              :socValueVisible="socValueVisible"
            />
          </template>
          <!-- Secondary Counters -->
          <div
            v-for="item in secondaryCounterData"
            :key="item.id"
            class="sub-row"
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
          :expand-separator="!props.desktop"
          v-model="expanded[item.id]"
          :class="[item.id, 'card']"
          :header-class="
            props.desktop || secondaryComponentsConfigured(item.id)
              ? 'cursor-pointer'
              : 'no-pointer'
          "
        >
          <template #header>
            <DailyTotalsRow
              :item="item"
              :rowHeight="rowHeight"
              :rowExpanded="expanded[item.id]"
              :hideDailyTotals="props.desktop && !expanded[item.id]"
              :secondaryComponentsConfigured="
                props.desktop || secondaryComponentsConfigured(item.id)
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
                <template v-else-if="['house', 'consumer'].includes(item.id)">
                  <div>Verbrauch:</div>
                </template>
              </template>
              <template #right-value>
                <div
                  v-if="
                    [
                      'battery',
                      'grid',
                      'house',
                      'chargepoint',
                      'consumer',
                    ].includes(item.id) && item.today !== undefined
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
            <div
              v-for="chargePointData in individualChargePointData"
              :key="chargePointData.id"
              class="sub-row"
            >
              <DailyTotalsRow
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
          </div>
          <div v-if="item.id === 'battery'">
            <div
              v-for="batteryData in individualBatteryData"
              :key="batteryData.id"
              class="sub-row"
            >
              <DailyTotalsRow
                :item="batteryData"
                :rowHeight="rowHeight"
                :componentNameVisible="componentNameVisible"
                :currentPowerVisible="currentPowerVisible"
                :socValueVisible="socValueVisible"
              >
                <template #right-label>
                  <div>Geladen:</div>
                  <div>Entladen:</div>
                </template>
                <template #right-value>
                  <div>{{ batteryData.today?.imported }}</div>
                  <div>{{ batteryData.today?.exported }}</div>
                </template>
              </DailyTotalsRow>
            </div>
          </div>
          <div v-if="item.id === 'pv'">
            <div
              v-for="pvData in individualPvData"
              :key="pvData.id"
              class="sub-row"
            >
              <DailyTotalsRow
                :item="pvData"
                :rowHeight="rowHeight"
                :componentNameVisible="componentNameVisible"
                :currentPowerVisible="currentPowerVisible"
                :socValueVisible="socValueVisible"
              >
                <template #right-label>
                  <div>Ertrag:</div>
                </template>
                <template #right-value>
                  <div>{{ pvData.today?.exported }}</div>
                </template>
              </DailyTotalsRow>
            </div>
          </div>
          <div v-if="item.id === 'consumer'">
            <div
              v-for="consumerData in individualConsumerData"
              :key="consumerData.id"
              class="sub-row"
            >
              <DailyTotalsRow
                :item="consumerData"
                :rowHeight="rowHeight"
                :componentNameVisible="componentNameVisible"
                :currentPowerVisible="currentPowerVisible"
                :socValueVisible="socValueVisible"
              >
                <template #right-label>
                  <div>Verbrauch:</div>
                </template>
                <template #right-value>
                  <div>{{ consumerData.today?.imported }}</div>
                </template>
              </DailyTotalsRow>
            </div>
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
import { useLocalDataStore } from 'src/stores/localData-store';
import DailyTotalsRow from './DailyTotalsRow.vue';
import type { DailyTotalsItem } from 'src/components/models/daily-totals-model';

const $q = useQuasar();
const props = defineProps<{ desktop?: boolean }>();
const mqttStore = useMqttStore();
const localDataStore = useLocalDataStore();
const gridPower = computed(() => mqttStore.counterPower('value'));
const showGrid = computed(
  () =>
    gridPower.value !== undefined ||
    secondaryComponentsConfigured.value('counter'),
);
const expanded = ref<Record<string, boolean>>({
  grid: false,
  chargepoint: false,
  battery: false,
  pv: false,
  consumer: false,
  ...Object.fromEntries(
    localDataStore.expandedDailyTotals.map((name) => [name, true]),
  ),
});
watch(
  expanded,
  (value) => {
    localDataStore.expandedDailyTotals = Object.keys(value).filter(
      (name) => value[name],
    );
  },
  { deep: true },
);

const componentNameVisible = computed(() => $q.screen.width >= 300);
const currentPowerVisible = computed(
  () => props.desktop || $q.screen.width >= 500,
);
const socValueVisible = computed(() => props.desktop || $q.screen.width >= 700);

const showHomePower = computed(() => {
  return mqttStore.homePower('value') !== undefined;
});
const batteryConfigured = computed(() => mqttStore.batteryConfigured);
const pvConfigured = computed(() => mqttStore.pvConfigured);
const consumerConfigured = computed(() => mqttStore.consumerIds.length > 0);
const chargePointSumPowerAvailable = computed(
  () => mqttStore.chargePointSumPower('value') !== undefined,
);
const chargePointConfigured = computed(
  () => mqttStore.chargePointIds.length > 0,
);
const secondaryComponentsConfigured = computed(() => {
  return (componentType: string): boolean => {
    switch (componentType) {
      case 'counter':
        return secondaryCounterData.value.length > 0;
      case 'chargepoint':
        return individualChargePointData.value.length > 1;
      case 'battery':
        return individualBatteryData.value.length > 1;
      case 'pv':
        return individualPvData.value.length > 1;
      case 'consumer':
        return individualConsumerData.value.length > 1;
      default:
        return false;
    }
  };
});

const gridData = computed((): DailyTotalsItem => {
  let data: DailyTotalsItem = {
    id: 'grid',
    title: 'Zähler',
    level: 'primary',
    icon: 'grid',
  };
  if (gridPower.value !== undefined) {
    data = {
      ...data,
      title: 'Netz',
      icon: 'grid',
      power: mqttStore.counterPower('textValue') as string,
      powerValue: mqttStore.counterPower('value') as number,
      today: {
        imported: mqttStore.counterDailyImported('textValue') as string,
        exported: mqttStore.counterDailyExported('textValue') as string,
      },
      color: 'var(--q-grid-stroke)',
    };
  }
  return data;
});

const secondaryCounterData = computed((): DailyTotalsItem[] => {
  const counters: DailyTotalsItem[] = [];
  mqttStore.secondaryCounterIds.forEach((id) => {
    const name = mqttStore.componentName(id);
    if (name !== undefined) {
      counters.push({
        id: `counter-${id}`,
        title: name,
        level: 'secondary',
        icon: 'counter',
        power: mqttStore.counterPower('textValue', id) as string,
        powerValue: mqttStore.counterPower('value', id) as number,
        today: {
          imported: mqttStore.counterDailyImported('textValue', id) as string,
          exported: mqttStore.counterDailyExported('textValue', id) as string,
        },
        color:
          mqttStore.gridComponentColor(id) ||
          'var(--q-secondary-counter-stroke)',
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
        level: 'secondary',
        icon: 'chargepoint',
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
        color: mqttStore.chargePointColor(id) || 'var(--q-charge-point-stroke)',
      });
    }
  });
  return chargePoints;
});

const individualBatteryData = computed((): DailyTotalsItem[] => {
  const batteries: DailyTotalsItem[] = [];

  mqttStore.batteryIds.forEach((id) => {
    const name = mqttStore.batteryName(id);
    if (name !== undefined) {
      batteries.push({
        id: `battery-${id}`,
        title: name,
        level: 'secondary',
        icon: 'battery',
        soc: mqttStore.batterySoc(id),
        power: mqttStore.batteryPower(id, 'textValue') as string,
        powerValue: mqttStore.batteryPower(id, 'value') as number,
        today: {
          imported: mqttStore.batteryDailyImported(id, 'textValue') as string,
          exported: mqttStore.batteryDailyExported(id, 'textValue') as string,
        },
        color: mqttStore.batteryColor(id) || 'var(--q-battery-stroke)',
      });
    }
  });
  return batteries;
});

const individualPvData = computed((): DailyTotalsItem[] => {
  const pvSystems: DailyTotalsItem[] = [];

  mqttStore.pvIds.forEach((id) => {
    const name = mqttStore.componentName(id);
    if (name !== undefined) {
      pvSystems.push({
        id: `pv-${id}`,
        title: name,
        level: 'secondary',
        icon: 'pv',
        power: mqttStore.pvPowerIndividual(id, 'textValue') as string,
        powerValue: mqttStore.pvPowerIndividual(id, 'value') as number,
        today: {
          exported: mqttStore.pvDailyExportedIndividual(
            id,
            'textValue',
          ) as string,
        },
        color: mqttStore.pvColor(id) || 'var(--q-pv-stroke)',
      });
    }
  });
  return pvSystems;
});

const individualConsumerData = computed((): DailyTotalsItem[] => {
  const consumers: DailyTotalsItem[] = [];

  mqttStore.consumerIds.forEach((id) => {
    const name = mqttStore.consumerName(id);
    if (name !== undefined) {
      consumers.push({
        id: `consumer-${id}`,
        title: name,
        level: 'secondary',
        icon: 'consumer',
        power: mqttStore.consumerPower(id, 'textValue') as string,
        powerValue: mqttStore.consumerPower(id, 'value') as number,
        today: {
          imported: mqttStore.consumerDailyImported('textValue', id) as string,
        },
        color: mqttStore.consumerColor(id) || 'var(--q-consumer)',
      });
    }
  });
  return consumers;
});

const componentData = computed((): DailyTotalsItem[] => {
  const components: DailyTotalsItem[] = [];

  if (batteryConfigured.value) {
    let item: DailyTotalsItem = {
      id: 'battery',
      title: 'Speicher',
      level: 'primary',
      icon: 'battery',
    };
    item = {
      ...item,
      soc: mqttStore.batterySocTotal,
      power: mqttStore.batteryTotalPower('textValue') as string,
      powerValue: mqttStore.batteryTotalPower('value') as number,
      today: {
        imported: mqttStore.batteryDailyImportedTotal('textValue') as string,
        exported: mqttStore.batteryDailyExportedTotal('textValue') as string,
      },
      color: 'var(--q-battery-stroke)',
    };
    components.push(item);
  }

  if (pvConfigured.value) {
    components.push({
      id: 'pv',
      title: 'PV',
      level: 'primary',
      icon: 'pv',
      power: mqttStore.pvPowerTotal('textValue') as string,
      powerValue: mqttStore.pvPowerTotal('value') as number,
      today: { exported: mqttStore.pvDailyExported('textValue') as string },
      color: 'var(--q-pv-stroke)',
    });
  }

  if (showHomePower.value) {
    components.push({
      id: 'house',
      title: 'Haus',
      level: 'primary',
      icon: 'house',
      power: mqttStore.homePower('textValue') as string,
      powerValue: mqttStore.homePower('value') as number,
      today: { imported: mqttStore.homeDailyYield('textValue') as string },
      color: 'var(--q-home-stroke)',
    });
  }

  if (chargePointConfigured.value || chargePointSumPowerAvailable.value) {
    let item: DailyTotalsItem = {
      id: 'chargepoint',
      title: mqttStore.chargePointIds.length > 1 ? 'Ladepunkte' : 'Ladepunkt',
      level: 'primary',
      icon: 'chargepoint',
      color:
        mqttStore.chargePointIds.length === 1
          ? mqttStore.chargePointColor(mqttStore.chargePointIds[0]) ||
            'var(--q-charge-point-stroke)'
          : 'var(--q-charge-point-stroke)',
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
      if (mqttStore.chargePointIds.length === 1) {
        item.color =
          mqttStore.chargePointColor(mqttStore.chargePointIds[0]) || undefined;
      }
    }
    components.push(item);
  }
  if (consumerConfigured.value) {
    components.push({
      id: 'consumer',
      title: 'Verbraucher',
      level: 'primary',
      icon: 'consumer',
      power: mqttStore.consumerSumPower('textValue') as string,
      powerValue: mqttStore.consumerSumPower('value') as number,
      today: {
        imported: mqttStore.consumerDailyImported('textValue') as string,
      },
      color:
        mqttStore.consumerIds.length === 1
          ? mqttStore.consumerColor(mqttStore.consumerIds[0]) ||
            'var(--q-consumer)'
          : 'var(--q-consumer)',
    });
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

// Recompute when rows or grid / chargepoint / battery expansion change
watch(
  () => ({
    rows: componentData.value.length + secondaryCounterData.value.length,
    expanded: expanded.value,
  }),
  () => calculateRowHeight(),
);
</script>

<style scoped>
.totals-desktop.container {
  height: auto;
  --totals-icon-size: 24px;
}
.totals-desktop .centered-panel {
  max-width: none;
  height: auto;
  overflow: visible;
}
.totals-desktop .scroll-container {
  display: grid;
  grid-template-columns: repeat(6, minmax(0, 1fr));
  align-items: start;
  gap: var(--dashboard-gap, 12px);
  max-height: none;
  overflow: visible;
  padding: 0;
}
.totals-desktop .card {
  margin-bottom: 0;
  min-width: 0;
}
.totals-desktop :deep(.component-container) {
  display: grid;
  grid-template-areas:
    'heading reading'
    'labels values';
  grid-template-columns: minmax(0, 1fr) auto;
  height: auto;
  min-height: 96px;
  gap: 0.5rem 0.2rem;
  padding: 0.6rem 0.5rem;
}
.totals-desktop :deep(.component-heading) {
  grid-area: heading;
  display: flex;
  align-items: center;
  gap: 8px;
  min-width: 0;
  line-height: 1.4;
}
.totals-desktop :deep(.col-icon) {
  flex: 0 0 var(--totals-icon-size);
  width: var(--totals-icon-size);
  height: var(--totals-icon-size);
  align-items: center;
}
.totals-desktop :deep(.col-title) {
  flex: 1 1 auto;
}
.totals-desktop :deep(.component-reading) {
  grid-area: reading;
  display: flex;
  align-items: center;
  justify-content: flex-end;
  gap: 4px;
  min-width: 0;
  font-size: 0.9rem;
  line-height: 1.4;
}
.totals-desktop :deep(.col-soc-spacer) {
  display: none;
}
.totals-desktop :deep(.col-soc),
.totals-desktop :deep(.col-arrow),
.totals-desktop :deep(.col-power) {
  display: flex;
  align-items: center;
  justify-content: flex-end;
  flex: 0 0 auto;
  line-height: 1.4;
}
.totals-desktop :deep(.col-arrow) {
  line-height: 1;
}
.totals-desktop :deep(.col-arrow .q-icon) {
  /* Align the arrow's visible centre with the adjacent numerals. */
  position: relative;
  top: -0.5px;
}
.totals-desktop :deep(.col-power) {
  font-size: 0.9rem;
  font-weight: 600;
}
.totals-desktop :deep(.col-flex) {
  display: none;
}
.totals-desktop :deep(.col-right-label) {
  grid-area: labels;
  text-align: left;
}
.totals-desktop :deep(.col-right-value) {
  grid-area: values;
}
.totals-desktop :deep(.col-title),
.totals-desktop :deep(.title-wrapper),
.totals-desktop :deep(.ellipsis-wrapper) {
  white-space: nowrap;
  min-width: 0;
}
.totals-desktop :deep(.base-icon) {
  display: block;
  width: var(--totals-icon-size) !important;
  height: var(--totals-icon-size) !important;
}
.totals-desktop :deep(.expand-icon) {
  flex-shrink: 0;
  font-size: 1rem;
}
.totals-desktop :deep(.col-title) {
  font-size: 0.85rem;
}
.totals-desktop .sub-row :deep(.component-container) {
  min-height: 96px;
}

.totals-desktop :deep(.totals-hidden) {
  grid-template-areas: 'heading reading';
  min-height: 52px;
}

@media (max-width: 1199px) {
  .totals-desktop .scroll-container {
    grid-template-columns: repeat(3, minmax(0, 1fr));
  }
}

@media (max-width: 599px) {
  .totals-desktop.container {
    --totals-icon-size: 20px;
  }
  .totals-desktop :deep(.component-container) {
    grid-template-areas:
      'heading heading'
      'reading reading'
      'labels labels'
      'values values';
    gap: 0.25rem 0.15rem;
    padding: 0.4rem 0.3rem;
  }
  .totals-desktop :deep(.totals-hidden) {
    grid-template-areas:
      'heading heading'
      'reading reading';
    min-height: 64px;
  }
  .totals-desktop :deep(.col-title) {
    font-size: 0.75rem;
  }
  .totals-desktop :deep(.component-reading) {
    font-size: 0.8rem;
  }
  .totals-desktop :deep(.col-power) {
    font-size: 0.8rem;
    white-space: nowrap;
  }
  .totals-desktop :deep(.col-soc) {
    font-size: 0.7rem;
  }
  .totals-desktop :deep(.col-right-label),
  .totals-desktop :deep(.col-right-value) {
    font-size: 0.75rem;
    text-align: left;
  }
}

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
  padding: 0 0.5rem 0.5rem 0.5rem;
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
.card {
  border-radius: 0.5rem;
  background: var(--q-card-background);
  filter: drop-shadow(0 0 0.15rem var(--q-chart-shadow));
  margin-bottom: 0.25rem;
}

.sub-row {
  border-top: 0.12rem solid var(--q-grey-4);
}
.rotate-180 {
  transform: rotate(180deg);
}
</style>
