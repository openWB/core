<template>
  <div
    class="flex column items-center justify-center container"
    ref="rootRef"
    :style="{ '--row-h': rowHeight + 'px' }"
  >
    <div class="centered-panel">
      <div
        class="flex justify-between text-subtitle1 text-weight-bold full-width"
        ref="titleRef"
      >
        <div v-if="currentPowerVisible">Aktuelle Leistung</div>
        <div>Tageswerte</div>
      </div>
      <q-table
        flat
        :rows="rows"
        :columns="columns"
        row-key="id"
        hide-header
        hide-bottom
        dense
        separator="none"
        class="banner-table theme-text"
      >
        <template #body="props">
          <q-tr
            :props="props"
            :class="props.row.id"
          >
            <q-td key="icon" :props="props">
              <img
                :src="props.row.icon"
                :alt="props.row.title"
                class="icon"
                :style="{ width: iconSize + 'px', height: iconSize + 'px' }"
              />
            </q-td>

            <q-td
              v-if="componentNameVisible"
              key="title"
              :props="props"
              class="text-body2 text-weight-bold"
            >
              {{ props.row.title }}
            </q-td>

            <q-td
              v-if="socValueVisible"
              key="soc"
              :props="props"
              class="text-right"
            >
              <span v-if="props.row.id === 'battery'"
                >{{ props.row.soc }}%</span
              >
            </q-td>

            <q-td v-if="currentPowerVisible" key="arrow" :props="props">
              <q-icon
                :name="
                  props.row.id === 'house'
                    ? 'horizontal_rule'
                    : arrowDirection(props.row.id).noCurrent
                      ? 'horizontal_rule'
                      : 'double_arrow'
                "
                :class="{
                  'rotate-180': arrowDirection(props.row.id).rotate180,
                }"
              />
            </q-td>

            <q-td
              v-if="currentPowerVisible"
              key="power"
              :props="props"
              class="text-right text-body2"
            >
              {{ String(props.row.power).replace('-', '') }}
            </q-td>

            <!-- Gap column stretches -->
            <q-td key="gap" :props="props"></q-td>

            <q-td
              key="rightLabel"
              :props="props"
              class="text-right text-weight-bold"
            >
              <template
                v-if="['battery', 'chargepoint'].includes(props.row.id)"
              >
                <div>Geladen:</div>
                <div>Entladen:</div>
              </template>
              <template v-else-if="props.row.id === 'grid'">
                <div>Bezug:</div>
                <div>Einspeisung:</div>
              </template>
              <template v-else-if="props.row.id === 'pv'">
                <div>Ertrag:</div>
              </template>
              <template v-else-if="props.row.id === 'house'">
                <div>Verbrauch:</div>
              </template>
            </q-td>

            <q-td key="rightValue" :props="props">
              <div
                v-if="
                  ['battery', 'grid', 'house', 'chargepoint'].includes(
                    props.row.id,
                  )
                "
              >
                {{ props.row.today.imported }}
              </div>
              <div
                v-if="
                  ['battery', 'grid', 'pv', 'chargepoint'].includes(
                    props.row.id,
                  )
                "
              >
                {{ props.row.today.exported }}
              </div>
            </q-td>
          </q-tr>
        </template>
      </q-table>
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
import type { QTableColumn } from 'quasar';
import type { DailyTotalsItem } from 'src/components/models/daily-totals-model';

const $q = useQuasar();
const mqttStore = useMqttStore();

const iconSize = ref(28);

const columns: QTableColumn<DailyTotalsItem>[] = [
  {
    name: 'icon',
    label: '',
    field: 'icon',
    align: 'left',
    style: 'width:32px;',
  },
  {
    name: 'title',
    label: '',
    field: 'title',
    align: 'left',
    style: 'width:80px;',
  },
  { name: 'soc', label: '', field: 'soc', align: 'right', style: 'width:6px;' },
  {
    name: 'arrow',
    label: '',
    field: 'arrow',
    align: 'center',
    style: 'width:24px;',
  },
  {
    name: 'power',
    label: '',
    field: 'power',
    align: 'right',
    style: 'width:20px;',
  },
  { name: 'gap', label: '', field: 'gap', align: 'left', style: 'width:auto;' },
  {
    name: 'rightLabel',
    label: '',
    field: 'rightLabel',
    align: 'right',
    style: 'width:100px;',
  },
  {
    name: 'rightValue',
    label: '',
    field: 'rightValue',
    align: 'right',
    style: 'width:70px;',
  },
];

const componentNameVisible = computed(() => $q.screen.width >= 375);
const currentPowerVisible = computed(() => $q.screen.width >= 500);
const socValueVisible = computed(() => $q.screen.width >= 700);

const batteryConfigured = computed(() => mqttStore.batteryConfigured);
const pvConfigured = computed(() => mqttStore.getPvConfigured);
const chargePointConfigured = computed(
  () => mqttStore.chargePointIds.length > 0,
);

const rows = computed((): DailyTotalsItem[] => {
  const components: DailyTotalsItem[] = [];

  components.push({
    id: 'grid',
    title: 'Netz',
    icon: 'icons/owbGrid.svg',
    power: mqttStore.getGridPower('textValue') as string,
    powerValue: mqttStore.getGridPower('value') as number,
    today: {
      imported: mqttStore.gridDailyImported('textValue') as string,
      exported: mqttStore.gridDailyExported('textValue') as string,
    },
  });

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

const getArrowDirection = computed(() =>
  rows.value.map((item) => {
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
  getArrowDirection.value.find((component) => component.id === itemId) ?? {
    rotate180: false,
    noCurrent: false,
  };

const rootRef = ref<HTMLElement | null>(null);
const titleRef = ref<HTMLElement | null>(null);
const rowHeight = ref(44);

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
    const verticalGaps = (rows.value.length - 1) * 3;
    const safetyPadding = 12;
    const availableHeight = Math.max(
      0,
      totalHeight - titleHeight - verticalGaps - safetyPadding,
    );
    const rowCount = Math.max(1, rows.value.length);
    const ROW_MIN = 36;
    const ROW_MAX = 65;
    rowHeight.value = Math.max(
      ROW_MIN,
      Math.min(ROW_MAX, Math.floor(availableHeight / rowCount)),
    );
  });
};

onMounted(() => {
  slideElement = getSlideElement();
  // Observe slide size changes (e.g. viewport resize, fullscreen, layout shifts)
  if (slideElement) {
    slideObserver = new ResizeObserver(calculateRowHeight);
    slideObserver.observe(slideElement);
  }
  // Fallback: also listen to window resize
  window.addEventListener('resize', calculateRowHeight, { passive: true });
  calculateRowHeight();
});

onBeforeUnmount(() => {
  slideObserver?.disconnect();
  slideObserver = null;
  window.removeEventListener('resize', calculateRowHeight);
});
// Recompute when number of rows changes (components shown/hidden)
watch(rows, calculateRowHeight, { deep: true });
</script>

<style scoped>
.container {
  min-height: 100%;
  overflow-y: auto;
}

.centered-panel {
  max-width: 600px;
  width: 100%;
}

.banner-table :deep(.q-table__middle table) {
  border-collapse: separate;
  border-spacing: 0 3px; /* vertical gap between “cards” */
}

.banner-table :deep(tbody tr) {
  height: var(--row-h);
}

.banner-table :deep(tbody td:first-child) {
  border-top-left-radius: 8px;
  border-bottom-left-radius: 8px;
}
.banner-table :deep(tbody td:last-child) {
  border-top-right-radius: 8px;
  border-bottom-right-radius: 8px;
}

.banner-table :deep(.q-table__container),
.banner-table :deep(.q-table__middle) {
  background: var(--q-background-2) !important;
}

.grid {
  background: #d5bbc0;
}
.body--dark .grid {
  background: #a13a41;
}

.battery {
  background: #c7a388;
}
.body--dark .battery {
  background: #b97a1f;
}

.pv {
  background: #b3ccbc;
}
.body--dark .pv {
  background: #27623a;
}

.house {
  background: #bababf;
}
.body--dark .house {
  background: #6e6e6e;
}

.chargepoint {
  background: #b1c0d6;
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
