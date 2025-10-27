<template>
  <div class="q-pa-md flex column items-center justify-center container">
    <div class="centered-panel">
      <div class="flex justify-between text-subtitle1 text-weight-bold full-width">
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
        <!-- Color each row like a banner -->
        <template #body="props">
          <q-tr
            :props="props"
            :style="{ '--row-bg': props.row.backgroundColor }"
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
              <template v-if="props.row.id === 'battery'">
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
                <div>Energie:</div>
              </template>
              <template v-else-if="props.row.id === 'chargepoint'">
                <div>Geladen:</div>
              </template>
            </q-td>

            <q-td key="rightValue" :props="props" class="text-right">
              <template v-if="props.row.id === 'battery'">
                <div>{{ props.row.today.charged }}</div>
                <div>{{ props.row.today.discharged }}</div>
              </template>
              <template v-else-if="props.row.id === 'grid'">
                <div>{{ props.row.today.imported }}</div>
                <div>{{ props.row.today.exported }}</div>
              </template>
              <template v-else-if="props.row.id === 'pv'">
                <div>{{ props.row.today.yield }}</div>
              </template>
              <template v-else-if="props.row.id === 'house'">
                <div>{{ props.row.today.energy }}</div>
              </template>
              <template v-else-if="props.row.id === 'chargepoint'">
                <div>{{ props.row.today.charged }}</div>
              </template>
            </q-td>
          </q-tr>
        </template>
      </q-table>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue';
import { useQuasar } from 'quasar';
import { useMqttStore } from 'src/stores/mqtt-store';
import type { QTableColumn } from 'quasar';
import type { DailyTotalsItem } from 'src/components/models/daily-totals-model';

const $q = useQuasar();
const mqttStore = useMqttStore();

const iconSize = computed(() => ($q.screen.width <= 500 ? 24 : 28));

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
    style: 'width: 11ch;',
  },
  {
    name: 'soc',
    label: '',
    field: 'soc',
    align: 'right',
    style: 'width: 6ch;',
  },
  {
    name: 'arrow',
    label: '',
    field: 'arrow',
    align: 'center',
    style: 'width: 24px;',
  },
  {
    name: 'power',
    label: '',
    field: 'power',
    align: 'right',
    style: 'width: 8ch;',
  },
  {
    name: 'gap',
    label: '',
    field: 'gap',
    align: 'left',
    style: 'width: auto;',
  },
  {
    name: 'rightLabel',
    label: '',
    field: 'rightLabel',
    align: 'right',
    style: 'width: 12ch',
  },
  {
    name: 'rightValue',
    label: '',
    field: 'rightValue',
    align: 'right',
    style: 'width: 10ch;',
  },
];

const currentPowerVisible = computed(() => $q.screen.width >= 500);
const socValueVisible = computed(() => $q.screen.width >= 700);

const rows = computed((): DailyTotalsItem[] => [
  {
    id: 'grid',
    title: 'Netz',
    icon: 'icons/owbGrid.svg',
    power: mqttStore.getGridPower('textValue') as string,
    powerValue: mqttStore.getGridPower('value') as number,
    today: {
      imported: mqttStore.gridDailyImported('textValue') as string,
      exported: mqttStore.gridDailyExported('textValue') as string,
    },
    backgroundColor: 'rgb(213,187,192)',
  },
  {
    id: 'battery',
    title: 'Speicher',
    icon: 'icons/owbBattery.svg',
    soc: mqttStore.batterySocTotal as number,
    power: mqttStore.batteryTotalPower('textValue') as string,
    powerValue: mqttStore.batteryTotalPower('value') as number,
    today: {
      charged: mqttStore.batteryDailyImportedTotal('textValue') as string,
      discharged: mqttStore.batteryDailyExportedTotal('textValue') as string,
    },
    backgroundColor: 'rgb(199,163,136)',
  },
  {
    id: 'pv',
    title: 'PV',
    icon: 'icons/owbPV.svg',
    power: mqttStore.getPvPower('textValue') as string,
    powerValue: mqttStore.getPvPower('value') as number,
    today: { yield: mqttStore.pvDailyExported('textValue') as string },
    backgroundColor: 'rgb(179,204,188)',
  },
  {
    id: 'house',
    title: 'Haus',
    icon: 'icons/owbHouse.svg',
    power: mqttStore.getHomePower('textValue') as string,
    powerValue: mqttStore.getHomePower('value') as number,
    today: { energy: mqttStore.homeDailyYield('textValue') as string },
    backgroundColor: 'rgb(186,186,191)',
  },
  {
    id: 'chargepoint',
    title: 'Ladepunkte',
    icon: 'icons/owbChargePoint.svg',
    power: mqttStore.chargePointSumPower('textValue') as string,
    powerValue: mqttStore.chargePointSumPower('value') as number,
    today: {
      charged: mqttStore.chargePointDailyImported('textValue') as string,
    },
    backgroundColor: 'rgb(177,192,214)',
  },
]);

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
  getArrowDirection.value.find((component) => component.id === itemId) ??
  ({ rotate180: false, noCurrent: false });
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
  border-spacing: 0 3px; /* <-- vertical gap between “cards” */
}

/* draw a rounded, colored card behind each row */
.banner-table :deep(tbody tr) {
  position: relative;
}
.banner-table :deep(tbody tr)::before {
  content: '';
  position: absolute;
  inset: 0;
  background: var(--row-bg);
  border-radius: 8px;
  box-shadow: 0 2px 5px rgba(0, 0, 0, 0.20);
}

.banner-table :deep(.q-table__container),
.banner-table :deep(.q-table__middle) {
  background: var(--q-background-2) !important;
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
