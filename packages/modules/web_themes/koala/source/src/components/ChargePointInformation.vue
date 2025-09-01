<template>
  <BaseCarousel
    v-if="chargePointIds.length <= cardViewBreakpoint"
    :items="chargePointIds"
  >
    <template #item="{ item }">
      <ChargePointCard :charge-point-id="item" full-height />
    </template>
  </BaseCarousel>

  <BaseTable
    v-else
    :items="chargePointIds"
    :row-data="tableRowData"
    :column-config="compactTable ? tableColumnsCompact : columnConfig"
    :dense="compactTable"
    :search-input-visible="searchInputVisible"
    :table-height="compactTable ? '35vh' : '45vh'"
    v-model:filter="filter"
    :columns-to-search="['vehicle', 'name']"
    :row-expandable="compactTable"
    @row-click="onRowClick"
  >
    <!-- full view table body slots -->
    <template #body-cell-plugged="slotProps">
      <q-td :class="`text-${slotProps.col.align}`">
        <ChargePointStateIcon :charge-point-id="slotProps.row.id" />
      </q-td>
    </template>

    <template #body-cell-chargeMode="slotProps">
      <q-td :class="`text-${slotProps.col.align}`">
        <ChargePointMode :charge-point-id="slotProps.row.id" />
      </q-td>
    </template>

    <template #body-cell-timeCharging="slotProps">
      <q-td :class="`text-${slotProps.col.align}`">
        <ChargePointTimeCharging
          :charge-point-id="slotProps.row.id"
          :readonly="true"
          :toolTip="true"
          :icon-size="'xs'"
        />
      </q-td>
    </template>

    <template #body-cell-powerColumn="slotProps">
      <q-td :class="`text-${slotProps.col.align}`">
        <ChargePointPowerData
          :power="slotProps.row.power"
          :phase-number="slotProps.row.phaseNumber"
          :current="slotProps.row.current"
          :column-display-format="isSmallScreen"
        />
      </q-td>
    </template>
    <!-- compact view table body slots -->
    <!-- compact view charge point name and vehicle name displayed in one field -->
    <template #body-cell-nameAndVehicle="slotProps">
      <q-td :class="`text-${slotProps.col.align}`">
        {{ slotProps.row.name }}<br />
        <span class="text-caption">{{ slotProps.row.vehicle }}</span>
      </q-td>
    </template>

    <!-- compact view charge point charge mode, plug status and time charging displayed in one field -->
    <template #body-cell-modePluggedTimeCharging="slotProps">
      <q-td :class="`text-${slotProps.col.align}`">
        <div class="items-center">
          <ChargePointMode :charge-point-id="slotProps.row.id" />
          <ChargePointStateIcon :charge-point-id="slotProps.row.id" />
          <ChargePointTimeCharging
            :charge-point-id="slotProps.row.id"
            :readonly="true"
            :toolTip="true"
            :icon-size="'xs'"
          />
        </div>
      </q-td>
    </template>

    <!-- Pass expansion row data to BaseTable.vue -->
    <template #row-expand="slotProps">
      <div class="q-pa-xs column q-gutter-y-xs">
        <div
          v-for="column in expansionColumnsCompact"
          :key="column.field"
          class="row items-start"
        >
          <!-- label ------------------------------------------------>
          <div class="col-5 text-caption text-bold">{{ column.label }}:</div>
          <!-- value --------------------------------------------------------->
          <div class="col-7 text-right">
            {{ slotProps.row[column.field] }}
          </div>
        </div>
      </div>
    </template>
  </BaseTable>

  <!-- ChargePointCard Dialog -->
  <q-dialog
    v-model="modalChargePointCardVisible"
    transition-show="fade"
    transition-hide="fade"
    :maximized="isSmallScreen"
    :full-height="isSmallScreen"
    :full-width="isSmallScreen"
    :backdrop-filter="$q.screen.width < 385 ? '' : 'blur(4px)'"
  >
    <ChargePointCard
      v-if="selectedChargePointId !== null"
      :charge-point-id="selectedChargePointId"
      :close-button="true"
    />
  </q-dialog>
</template>

<script setup lang="ts">
import { computed, ref } from 'vue';
import { Screen } from 'quasar';
import { useMqttStore } from 'src/stores/mqtt-store';
import { useChargeModes } from 'src/composables/useChargeModes';
import BaseCarousel from 'src/components/BaseCarousel.vue';
import BaseTable from 'src/components/BaseTable.vue';
import ChargePointCard from 'src/components/ChargePointCard.vue';
import ChargePointStateIcon from 'src/components/ChargePointStateIcon.vue';
import ChargePointMode from './ChargePointMode.vue';
import ChargePointTimeCharging from './ChargePointTimeCharging.vue';
import ChargePointPowerData from './ChargePointPowerData.vue';
import {
  ColumnConfiguration,
  ChargePointRow,
} from 'src/components/models/table-model';

const mqttStore = useMqttStore();
const { chargeModes } = useChargeModes();
const chargePointIds = computed(() => mqttStore.chargePointIds);
const cardViewBreakpoint = computed(
  () => mqttStore.themeConfiguration?.chargePoint_card_view_breakpoint || 4,
);
const searchInputVisible = computed(
  () => mqttStore.themeConfiguration?.chargePoint_table_search_input_field,
);
const isSmallScreen = computed(() => Screen.lt.sm);
const compactTable = computed(() => Screen.lt.md);
const selectedChargePointId = ref<number | null>(null);
const modalChargePointCardVisible = ref(false);
const filter = ref('');

const tableRowData = computed<(id: number) => ChargePointRow>(() => {
  return (id: number) => {
    const name = mqttStore.chargePointName(id);
    const vehicle =
      mqttStore.chargePointConnectedVehicleInfo(id).value?.name ||
      'Kein Fahrzeug';
    const plugged = mqttStore.chargePointPlugState(id);
    const chargeModeValue =
      mqttStore.chargePointConnectedVehicleChargeMode(id).value;
    const chargeModeObj = chargeModes.find(
      (mode) => mode.value === chargeModeValue,
    );
    const chargeMode = chargeModeObj ? chargeModeObj.label : chargeModeValue;
    const chargePointSoc =
      mqttStore.chargePointConnectedVehicleSoc(id).value?.soc;
    const soc =
      chargePointSoc !== undefined ? `${Math.round(chargePointSoc)}%` : '0%';
    // typecasting necessary as chargePointPower has a union type in store and needs to be narrowed to string
    const power = mqttStore.chargePointPower(id) as string;
    const charged = mqttStore.chargePointEnergyChargedPlugged(id) as string;
    const timeCharging =
      mqttStore.chargePointConnectedVehicleTimeCharging(id).value;
    const phaseNumber = mqttStore.chargePointPhaseNumber(id);
    // typecasting necessary as chargePointChargingCurrent has a union type in store and needs to be narrowed to string
    const current = mqttStore.chargePointChargingCurrent(id) as string;
    const powerColumn = '';
    return {
      id,
      name,
      vehicle,
      plugged,
      chargeMode,
      timeCharging,
      soc,
      power,
      phaseNumber,
      current,
      powerColumn,
      charged,
    };
  };
});

const columnConfig: ColumnConfiguration[] = [
  { field: 'name', label: 'Ladepunkt' },
  { field: 'vehicle', label: 'Fahrzeug' },
  { field: 'plugged', label: 'Status', align: 'center' },
  { field: 'chargeMode', label: 'Lademodus' },
  { field: 'timeCharging', label: 'Zeitladen', align: 'center' },
  { field: 'powerColumn', label: 'Leistung', align: 'right' },
  { field: 'charged', label: 'Geladen', align: 'right' },
  { field: 'soc', label: 'Ladestand', align: 'right' },
];

const columnConfigCompact: ColumnConfiguration[] = [
  { field: 'nameAndVehicle', label: 'Ladepunkt' },
  { field: 'modePluggedTimeCharging', label: 'Lademodus', align: 'center' },
  {
    field: 'powerColumn',
    label: 'Leistung',
    align: 'center',
  },
  { field: 'charged', label: 'Geladen', align: 'right', expandField: true },
  { field: 'soc', label: 'Ladestand', align: 'right', expandField: true },
];

const tableColumnsCompact = columnConfigCompact.filter(
  (column) => !column.expandField,
);
const expansionColumnsCompact = columnConfigCompact.filter(
  (column) => column.expandField,
);

const onRowClick = (row: ChargePointRow) => {
  selectedChargePointId.value = row.id;
  modalChargePointCardVisible.value = true;
};
</script>
