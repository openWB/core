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
    :column-config="mobile ? columnConfigMobile : columnConfigDesktop"
    :search-input-visible="searchInputVisible"
    :table-height="mobile ? '35vh' : '40vh'"
    v-model:filter="filter"
    :columns-to-search="['vehicle', 'name']"
    :row-expandable="mobile"
    @row-click="onRowClick"
  >
    <template #body-cell-plugged="{ row, col }">
      <q-td :class="`text-${col.align}`">
        <ChargePointStateIcon :charge-point-id="(row.id as number)" />
      </q-td>
    </template>

    <template #body-cell-timeCharging="{ row, col }">
      <q-td :class="`text-${col.align}`">
        <ChargePointTimeCharging
          :charge-point-id="(row.id as number)"
          :readonly="true"
          :toolTip="true"
          :icon-size="'xs'"
        />
      </q-td>
    </template>

    <template #body-cell-powerColumn="{ row, col }">
      <q-td :class="`text-${col.align}`">
        <ChargePointPowerData
          :power="(row.power as string)"
          :phase-number="(row.phaseNumber as number)"
          :current="(row.current as string)"
        />
      </q-td>
    </template>

    <!-- Pass expansion row data to BaseTable.vue --------------------------------------------------------->
    <template #row-expand="{ row }">
      <div v-if="mobile" class="q-pa-xs column q-gutter-y-xs">
        <div
          v-for="field in columnConfigMobile?.fieldsExpansionRow"
          :key="field"
          class="row items-start"
        >
          <!-- label ------------------------------------------------>
          <div class="col-5 text-caption text-bold">
            {{ columnConfigMobile?.labels?.[field] }}:
          </div>

          <!-- value --------------------------------------------------------->
          <div class="col-7 text-right">
            <ChargePointPowerData
              v-if="field === 'powerColumn'"
              :power="(row.power as string)"
              :phase-number="(row.phaseNumber as number)"
              :current="(row.current as string)"
            />
            <ChargePointTimeCharging
              v-if="field === 'timeCharging'"
              :charge-point-id="(row.id as number)"
              readonly
              icon-size="xs"
            />
            <span v-else>{{ row[field] }}</span>
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
import ChargePointPowerData from './ChargePointPowerData.vue';
import { columnConfig } from 'src/components/Models/base-table-model';

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
    const timeCharging =
      mqttStore.chargePointConnectedVehicleTimeCharging(id).value;
    const phaseNumber = mqttStore.chargePointPhaseNumber(id);
    const current = mqttStore.chargePointChargingCurrent(id, 'textValue');
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

const columnConfigDesktop: columnConfig = {
  fields: [
    'name',
    'vehicle',
    'plugged',
    'chargeMode',
    'timeCharging',
    'powerColumn',
    'charged',
    'soc',
  ],
  labels: {
    name: 'Ladepunkt',
    vehicle: 'Fahrzeug',
    plugged: 'Status',
    chargeMode: 'Lademodus',
    timeCharging: 'Zeitladen',
    powerColumn: 'Leistung',
    charged: 'Geladen',
    soc: 'Ladestand',
  },
  align: {
    plugged: 'center',
    timeCharging: 'center',
    soc: 'right',
    charged: 'right',
    powerColumn: 'right',
  },
};

const columnConfigMobile: columnConfig = {
  fields: ['name', 'vehicle', 'plugged'],
  fieldsExpansionRow: [
    'powerColumn',
    'chargeMode',
    'charged',
    'soc',
    'timeCharging',
  ],
  labels: {
    name: 'Ladepunkt',
    vehicle: 'Fahrzeug',
    plugged: 'Status',
    chargeMode: 'Lademodus',
    timeCharging: 'Zeitladen',
    powerColumn: 'Leistung',
    charged: 'Geladen',
    soc: 'Ladestand',
  },
  align: {
    plugged: 'center',
    timeCharging: 'center',
    soc: 'right',
    charged: 'right',
    powerColumn: 'right',
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
