<template>
  <BaseCarousel
    v-if="vehicleIds.length <= cardViewBreakpoint"
    :items="vehicleIds"
  >
    <template #item="{ item }">
      <VehicleCard :vehicle-id="item" full-height />
    </template>
  </BaseCarousel>

  <BaseTable
    v-else
    :items="vehicleIds"
    :row-data="tableRowData"
    :column-config="compactTable ? columnConfigCompact : columnConfig"
    :dense="compactTable"
    :square="compactTable"
    :search-input-visible="searchInputVisible"
    :table-height="compactTable ? '35vh' : '45vh'"
    v-model:filter="filter"
    :columns-to-search="['name', 'manufacturer', 'model']"
    :row-expandable="true"
    @row-click="onRowClick"
    :row-color="(row) => row.color"
  >
    <!-- "col" = column must match Quasar naming convention -->
    <template #row-expand="slotProps">
      <VehicleConnectionStateIcon :vehicle-id="slotProps.row.id" />
    </template>
    <template #body-cell-name="slotProps">
      <div class="row items-center no-wrap">
        <div class="ellipsis q-ml-sm" :title="slotProps.row.name">
          {{ slotProps.row.name }}
        </div>
      </div>
    </template>
    <template #body-cell-manufacturer="slotProps">
      {{ slotProps.row.manufacturer }}
    </template>
    <template #body-cell-model="slotProps">
      {{ slotProps.row.model }}
    </template>
    <template #body-cell-plugged="slotProps">
      <ChargePointStateIcon :vehicle-id="slotProps.row.id" />
    </template>
    <template #body-cell-vehicleSocValue="slotProps">
      {{ slotProps.row.vehicleSocValue }}
    </template>
  </BaseTable>

  <!-- VehicleCard Dialog -->
  <q-dialog
    v-model="modalChargeVehicleCardVisible"
    transition-show="fade"
    transition-hide="fade"
    :backdrop-filter="$q.screen.width < 385 ? '' : 'blur(4px)'"
  >
    <div class="dialog-content">
      <VehicleCard
        v-if="selectedVehicleId !== null"
        :vehicle-id="selectedVehicleId"
        closeButton
      />
    </div>
  </q-dialog>
</template>

<script setup lang="ts">
import { computed, ref } from 'vue';
import { useMqttStore } from 'src/stores/mqtt-store';
import { Screen } from 'quasar';
import BaseCarousel from 'src/components/BaseCarousel.vue';
import BaseTable from 'src/components/BaseTable.vue';
import { VehicleRow } from 'src/components/models/table-model';
import ChargePointStateIcon from 'src/components/ChargePointStateIcon.vue';
import VehicleConnectionStateIcon from './VehicleConnectionStateIcon.vue';
import VehicleCard from 'src/components/VehicleCard.vue';
import { ColumnConfiguration } from 'src/components/models/table-model';

const mqttStore = useMqttStore();
const compactTable = computed(() => Screen.lt.md);
const modalChargeVehicleCardVisible = ref(false);
const selectedVehicleId = ref<number | null>(null);
const filter = ref('');
const searchInputVisible = computed(
  () => mqttStore.themeConfiguration?.vehicle_table_search_input_field,
);
const cardViewBreakpoint = computed(
  () => mqttStore.themeConfiguration?.vehicle_card_view_breakpoint || 4,
);
const vehicles = computed(() => mqttStore.vehicleList);
const vehicleIds = computed(() => vehicles.value.map((vehicle) => vehicle.id));

const tableRowData = computed<(id: number) => VehicleRow>(() => {
  return (id: number) => {
    const vehicle = mqttStore.vehicleList.find((vehicle) => vehicle.id === id);
    const name = vehicle?.name || 'keine Angabe';
    const vehicleState = mqttStore.vehicleConnectionState(id);
    const plugState = vehicleState.some((vehicle) => vehicle.plugged);
    const chargeState = vehicleState.some((vehicle) => vehicle.charging);
    const info = mqttStore.vehicleInfo(id);
    const manufacturer = info?.manufacturer || 'keine Angabe';
    const model = info?.model || 'keine Angabe';
    const soc = mqttStore.vehicleSocValue(id);
    const vehicleSocValue = soc !== undefined ? `${Math.round(soc)}%` : '–';
    const color = mqttStore.vehicleColor(id) || 'var(--q-vehicle-stroke)';
    return {
      id,
      name,
      manufacturer,
      model,
      plugState,
      chargeState,
      vehicleSocValue,
      color,
    };
  };
});

const columnConfig: ColumnConfiguration[] = [
  { field: 'name', label: 'Fahrzeug', shrink: true },
  { field: 'manufacturer', label: 'Hersteller', autoWidth: true },
  { field: 'model', label: 'Modell', autoWidth: true },
  { field: 'plugged', label: 'Status', align: 'center', autoWidth: true },
  {
    field: 'vehicleSocValue',
    label: 'Ladestand',
    align: 'right',
    autoWidth: true,
  },
];

const columnConfigCompact: ColumnConfiguration[] = [
  { field: 'name', label: 'Fahrzeug' },
  { field: 'plugged', label: 'Status', align: 'center', autoWidth: true },
  {
    field: 'vehicleSocValue',
    label: 'Ladestand',
    align: 'right',
    autoWidth: true,
  },
];

const onRowClick = (row: VehicleRow) => {
  selectedVehicleId.value = row.id;
  modalChargeVehicleCardVisible.value = true;
};
</script>
