<template>
  <BaseCarousel
    v-if="chargePointIds.length <= cardViewBreakpoint"
    :items="chargePointIds"
  >
    <template #item="{ item }">
      <ChargePointCard :charge-point-id="item" />
    </template>
  </BaseCarousel>

  <BaseTable
    v-else
    :items="chargePointIds"
    :row-data="tableRowData"
    :column-config="mobile ? columnConfigMobile : columnConfig"
    :search-input-visible="searchInputVisible"
    :table-height="mobile ? '35vh' : '40vh'"
    v-model:filter="filter"
    :columns-to-search="['vehicle', 'name']"
    @row-click="onRowClick"
  >
    <template #body-cell-plugged="{ row, columnAlignment }">
      <q-td :class="`text-${columnAlignment}`">
        <ChargePointStateIcon :charge-point-id="row.id" />
      </q-td>
    </template>
    <template #body-cell-timeCharging="{ row, columnAlignment }">
      <q-td :class="`text-${columnAlignment}`">
        <ChargePointTimeCharging
          :charge-point-id="row.id"
          :readonly="true"
          :toolTip="true"
          :icon-size="'xs'"
        />
      </q-td>
    </template>
  </BaseTable>

  <!-- ChargePointCard Dialog -->
  <q-dialog
    v-model="modalChargePointCardVisible"
    transition-show="fade"
    transition-hide="fade"
    :backdrop-filter="$q.screen.width < 385 ? '' : 'blur(4px)'"
  >
    <div class="dialog-content">
      <ChargePointCard
        v-if="selectedChargePointId !== null"
        :charge-point-id="selectedChargePointId"
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
      </ChargePointCard>
    </div>
  </q-dialog>
</template>

<script setup lang="ts">
import { computed, ref } from 'vue';
import { Platform } from 'quasar';
import { useMqttStore } from 'src/stores/mqtt-store';
import { useChargeModes } from 'src/composables/useChargeModes';
import BaseCarousel from 'src/components/BaseCarousel.vue';
import BaseTable from 'src/components/BaseTable.vue';
import ChargePointCard from 'src/components/ChargePointCard.vue';
import ChargePointStateIcon from 'src/components/ChargePointStateIcon.vue';
import ChargePointTimeCharging from './ChargePointTimeCharging.vue';

const mqttStore = useMqttStore();
const { chargeModes } = useChargeModes();
const chargePointIds = computed(() => mqttStore.chargePointIds);
const cardViewBreakpoint = computed(
  () => mqttStore.themeConfiguration?.chargePoint_card_view_breakpoint || 4,
);
const searchInputVisible = computed(
  () => mqttStore.themeConfiguration?.chargePoint_table_search_input_field,
);
const mobile = computed(() => Platform.is.mobile);
const selectedChargePointId = ref<number | null>(null);
const modalChargePointCardVisible = ref(false);
const filter = ref('');
const tableRowData = computed(() => {
  return (id: number) => {
    const name = mqttStore.chargePointName(id);
    const vehicle =
      mqttStore.chargePointConnectedVehicleInfo(id).value?.name ||
      'Kein Fahrzeug';
    const plugged = mqttStore.chargePointPlugState(id) ? 'Ja' : 'Nein';
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
    const power = mqttStore.chargePointPower(id, 'textValue');
    const charged = mqttStore.chargePointEnergyChargedPlugged(id, 'textValue');
    const timeCharging = mqttStore.chargePointConnectedVehicleTimeCharging(id);
    return {
      id,
      name,
      vehicle,
      plugged,
      chargeMode,
      timeCharging,
      soc,
      power,
      charged,
    };
  };
});

//type AlignmentType = 'left' | 'right' | 'center';

const columnConfig = {
  fields: [
    'name',
    'vehicle',
    'plugged',
    'chargeMode',
    'timeCharging',
    'soc',
    'power',
    'charged',
  ],
  labels: {
    name: 'Ladepunkt',
    vehicle: 'Fahrzeug',
    plugged: 'Status',
    chargeMode: 'Lademodus',
    timeCharging: 'Zeitladen',
    soc: 'Ladestand',
    power: 'Leistung',
    charged: 'Geladen',
  },
  align: {
    plugged: 'center',
    timeCharging: 'center',
    soc: 'right',
    power: 'right',
    charged: 'right',
  },
};

const columnConfigMobile = {
  fields: ['name', 'vehicle', 'plugged'],
  labels: {
    name: 'Ladepunkt',
    vehicle: 'Fahrzeug',
    plugged: 'Status',
  },

};

const onRowClick = (row: Record<string, unknown>) => {
  selectedChargePointId.value = row.id as number;
  modalChargePointCardVisible.value = true;
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
