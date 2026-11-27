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
            secondaryComponentsConfigured('counter')
              ? 'cursor-pointer'
              : 'no-pointer'
          "
        >
          <template #header>
            <DailyTotalsRow
              :item="gridData"
              :rowHeight="rowHeight"
              :rowExpanded="expanded.grid"
              :secondaryComponentsConfigured="
                secondaryComponentsConfigured('counter')
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
          expand-separator
          v-model="expanded[item.id]"
          :class="[item.id, 'card']"
          :header-class="
            secondaryComponentsConfigured(item.id)
              ? 'cursor-pointer'
              : 'no-pointer'
          "
        >
          <template #header>
            <DailyTotalsRow
              :item="item"
              :rowHeight="rowHeight"
              :rowExpanded="expanded[item.id]"
              :secondaryComponentsConfigured="
                secondaryComponentsConfigured(item.id)
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
import DailyTotalsRow from './DailyTotalsRow.vue';
import { useDailyTotalsData } from 'src/composables/useDailyTotalsData';

const $q = useQuasar();
const expanded = ref<Record<string, boolean>>({
  grid: false,
  chargepoint: false,
  battery: false,
  pv: false,
  consumer: false,
});

const componentNameVisible = computed(() => $q.screen.width >= 300);
const currentPowerVisible = computed(() => $q.screen.width >= 500);
const socValueVisible = computed(() => $q.screen.width >= 700);

const {
  showGrid,
  gridData,
  secondaryCounterData,
  individualChargePointData,
  individualBatteryData,
  individualPvData,
  individualConsumerData,
  componentData,
  secondaryComponentsConfigured,
} = useDailyTotalsData();

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
