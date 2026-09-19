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
    :square="compactTable"
    :search-input-visible="searchInputVisible"
    :table-height="compactTable ? '35vh' : '45vh'"
    v-model:filter="filter"
    :columns-to-search="['vehicle', 'name']"
    :row-expandable="compactTable"
    @row-click="onRowClick"
    :row-color="(row) => row.color"
  >
    <!-- full view table body slots -->
    <template #body-cell-name="slotProps">
      <div class="row items-center no-wrap">
        <ChargePointFaultIcon
          v-if="faultPresent"
          :charge-point-id="slotProps.row.id"
          class="q-mr-xs"
        />
        <div class="col ellipsis" @mouseenter="titleIfTruncated">
          {{ slotProps.row.name }}
        </div>
        <q-tooltip v-if="slotProps.row.faultState > 0 && tooltipsEnabled">
          {{ slotProps.row.faultMessage }}
        </q-tooltip>
      </div>
    </template>
    <template #body-cell-vehicle="slotProps">
      <div class="ellipsis" @mouseenter="titleIfTruncated">
        {{ slotProps.row.vehicle }}
      </div>
    </template>
    <template #body-cell-plugged="slotProps">
      <ChargePointStateIcon :charge-point-id="slotProps.row.id" />
    </template>

    <template #body-cell-chargeMode="slotProps">
      <ChargePointMode :charge-point-id="slotProps.row.id" />
    </template>

    <template #body-cell-timeCharging="slotProps">
      <ChargePointTimeCharging
        :charge-point-id="slotProps.row.id"
        :readonly="true"
        :toolTip="true"
        :icon-size="'xs'"
      />
    </template>

    <template #body-cell-powerColumn="slotProps">
      <ChargePointPowerData
        :power="slotProps.row.power"
        :phase-number="slotProps.row.phaseNumber"
        :current="slotProps.row.current"
        :column-display-format="isSmallScreen"
      />
    </template>
    <template #body-cell-charged="slotProps">
      {{ slotProps.row.charged }}
    </template>
    <template #body-cell-soc="slotProps">
      {{ slotProps.row.soc }}
    </template>
    <!-- compact view table body slots -->
    <!-- compact view charge point name and vehicle name displayed in one field -->
    <template #body-cell-nameAndVehicle="slotProps">
      <div class="row items-center no-wrap">
        <ChargePointFaultIcon
          v-if="faultPresent"
          :charge-point-id="slotProps.row.id"
          class="q-mr-xs"
        />
        <div class="col">
          <div class="ellipsis" @mouseenter="titleIfTruncated">
            {{ slotProps.row.name }}
          </div>
          <div class="ellipsis text-caption" @mouseenter="titleIfTruncated">
            {{ slotProps.row.vehicle }}
          </div>
        </div>
        <q-tooltip v-if="slotProps.row.faultState > 0 && tooltipsEnabled">
          {{ slotProps.row.faultMessage }}
        </q-tooltip>
      </div>
    </template>

    <!-- compact view charge point charge mode, plug status and time charging displayed in one field -->
    <template #body-cell-modePluggedTimeCharging="slotProps">
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
import { Screen, useQuasar } from 'quasar';
import { useMqttStore } from 'src/stores/mqtt-store';
import { useChargeModes } from 'src/composables/useChargeModes';
import BaseCarousel from 'src/components/BaseCarousel.vue';
import BaseTable from 'src/components/BaseTable.vue';
import ChargePointCard from 'src/components/ChargePointCard.vue';
import ChargePointStateIcon from 'src/components/ChargePointStateIcon.vue';
import ChargePointMode from './ChargePointMode.vue';
import ChargePointTimeCharging from './ChargePointTimeCharging.vue';
import ChargePointPowerData from './ChargePointPowerData.vue';
import ChargePointFaultIcon from './ChargePointFaultIcon.vue';
import {
  ColumnConfiguration,
  ChargePointRow,
} from 'src/components/models/table-model';

const $q = useQuasar();

const tooltipsEnabled = !$q.platform.is.mobile;

const mqttStore = useMqttStore();
const { chargeModes } = useChargeModes();
const chargePointIds = computed(() => mqttStore.chargePointIds);
const cardViewBreakpoint = computed(
  () => mqttStore.themeConfiguration?.chargePoint_card_view_breakpoint || 4,
);
const searchInputVisible = computed(
  () => mqttStore.themeConfiguration?.chargePoint_table_search_input_field,
);

const faultPresent = computed(() =>
  chargePointIds.value.some((id) => mqttStore.chargePointFaultState(id) > 0),
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
    const faultState = mqttStore.chargePointFaultState(id);
    const faultMessage = mqttStore.chargePointFaultMessage(id) ?? '';
    const color =
      mqttStore.chargePointColor(id) || 'var(--q-charge-point-stroke)';
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
      faultState,
      faultMessage,
      color,
    };
  };
});

const columnConfig: ColumnConfiguration[] = [
  { field: 'name', label: 'Ladepunkt', shrink: true },
  { field: 'vehicle', label: 'Fahrzeug', autoWidth: true },
  { field: 'plugged', label: 'Status', align: 'center', autoWidth: true },
  { field: 'chargeMode', label: 'Lademodus', autoWidth: true },
  {
    field: 'timeCharging',
    label: 'Zeitladen',
    align: 'center',
    autoWidth: true,
  },
  { field: 'powerColumn', label: 'Leistung', align: 'right', autoWidth: true },
  { field: 'charged', label: 'Geladen', align: 'right', autoWidth: true },
  { field: 'soc', label: 'Ladestand', align: 'right', autoWidth: true },
];

const columnConfigCompact: ColumnConfiguration[] = [
  { field: 'nameAndVehicle', label: 'Ladepunkt', shrink: true },
  {
    field: 'modePluggedTimeCharging',
    label: 'Lademodus',
    align: 'center',
    autoWidth: true,
  },
  {
    field: 'powerColumn',
    label: 'Leistung',
    align: 'center',
    autoWidth: true,
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

// the browser tooltip is only set if the text is really cut off by the
// ellipsis, otherwise it would pop up next to the fault message tooltip
// without adding any information
const titleIfTruncated = (event: MouseEvent) => {
  const element = event.currentTarget as HTMLElement;
  const text = element.textContent?.trim() ?? '';
  // one pixel tolerance, scrollWidth and clientWidth are rounded values
  if (text && element.scrollWidth - element.clientWidth > 1) {
    element.title = text;
  } else {
    element.removeAttribute('title');
  }
};

const onRowClick = (row: ChargePointRow) => {
  selectedChargePointId.value = row.id;
  modalChargePointCardVisible.value = true;
};
</script>
