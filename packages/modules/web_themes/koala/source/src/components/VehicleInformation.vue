<template>
  <BaseCarousel
    v-if="vehicleIds.length <= cardViewBreakpoint"
    :items="vehicleIds"
  >
    <template #item="{ item }">
      <VehicleCard :vehicle-id="item" />
    </template>
  </BaseCarousel>

  <BaseTable
    v-else
    :items="vehicleIds"
    :row-data="tableRowData"
    :column-config="mobile ? columnConfigMobile : columnConfigDesktop"
    :search-input-visible="searchInputVisible"
    :table-height="mobile ? '35vh' : '40vh'"
    v-model:filter="filter"
    :columns-to-search="['name', 'manufacturer', 'model']"
    :row-expandable="true"
    @row-click="onRowClick"
  >
    <template #body-cell-plugged="{ row, col }">
      <q-td :class="`text-${col.align}`">
        <ChargePointStateIcon :vehicle-id="(row.id as number)" />
      </q-td>
    </template>
    <template #row-expand="{ row }">
      <VehicleConnectionStateIcon :vehicle-id="(row.id as number)" />
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
      >
        <template #card-footer>
          <div class="card-footer">
            <q-btn
              color="primary"
              flat
              no-caps
              v-close-popup
              class="close-button"
              size="md"
              >Schließen</q-btn
            >
          </div>
        </template>
      </VehicleCard>
    </div>
  </q-dialog>
</template>

<script setup lang="ts">
import { computed, ref } from 'vue';
import { useMqttStore } from 'src/stores/mqtt-store';
import { Platform } from 'quasar';
import BaseCarousel from 'src/components/BaseCarousel.vue';
import BaseTable from 'src/components/BaseTable.vue';
import ChargePointStateIcon from 'src/components/ChargePointStateIcon.vue';
import VehicleConnectionStateIcon from './VehicleConnectionStateIcon.vue';
import VehicleCard from 'src/components/VehicleCard.vue';
import { columnConfig } from 'src/components/Models/base-table-model';

const mqttStore = useMqttStore();
const mobile = computed(() => Platform.is.mobile);
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
const tableRowData = computed(() => {
  return (id: number) => {
    const vehicle = mqttStore.vehicleList.find((v) => v.id === id);
    const name = vehicle?.name || 'keine Angabe';
    const vehicleState = mqttStore.vehicleConnectionState(id);
    const plugState = vehicleState.some((v) => v.plugged);
    const chargeState = vehicleState.some((v) => v.charging);
    const info = mqttStore.vehicleInfo(id);
    const manufacturer = info?.manufacturer || 'keine Angabe';
    const model = info?.model || 'keine Angabe';
    const soc = mqttStore.vehicleSocValue(id);
    const vehicleSocValue = soc !== undefined ? `${Math.round(soc)}%` : '–';
    return {
      id,
      name,
      manufacturer,
      model,
      plugState,
      chargeState,
      vehicleSocValue,
    };
  };
});

const columnConfigDesktop: columnConfig = {
  fields: ['name', 'manufacturer', 'model', 'plugged', 'vehicleSocValue'],
  labels: {
    name: 'Fahrzeug',
    manufacturer: 'Hersteller',
    model: 'Modell',
    plugged: 'Status',
    vehicleSocValue: 'Ladestand',
  },
  align: {
    plugged: 'center',
    vehicleSocValue: 'right',
  },
};

const columnConfigMobile: columnConfig = {
  fields: ['name', 'plugged', 'vehicleSocValue'],
  labels: {
    name: 'Fahrzeug',
    plugged: 'Status',
    vehicleSocValue: 'Ladestand',
  },
  align: {
    plugged: 'center',
    vehicleSocValue: 'right',
  },
};

const onRowClick = (row: Record<string, unknown>) => {
  selectedVehicleId.value = row.id as number;
  modalChargeVehicleCardVisible.value = true;
};
</script>

<style scoped>
.dialog-content {
  width: auto;
  max-width: 24em;
}

.close-button {
  position: absolute;
  bottom: 0.4em;
  right: 0.4em;
  z-index: 1;
  background: transparent;
}

.card-footer {
  height: 1.9em;
}
</style>
