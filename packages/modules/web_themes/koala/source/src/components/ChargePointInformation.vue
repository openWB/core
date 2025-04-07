<template>
  <div>
    <BaseCarousel
      v-if="chargePointIds.length <= cardViewBreakpoint"
      :items="chargePointIds"
    >
      <template #item="{ item }">
        <ChargePointCard :charge-point-id="item" />
      </template>
    </BaseCarousel>

    <div v-else class="q-pa-md">
      <q-table
        class="sticky-header-table"
        :rows="rows"
        :columns="mobile ? columnsMobile : columns"
        row-key="id"
        :filter="filter"
        virtual-scroll
        :virtual-scroll-item-size="48"
        :virtual-scroll-sticky-size-start="48"
        :style="{ height: mobile ? '35vh' : '40vh' }"
        @row-click="onRowClick"
        binary-state-sort
        :pagination="{ rowsPerPage: 0 }"
        hide-bottom
      >
        <template v-slot:top v-if="searchInputVisible">
          <div class="row full-width items-center q-mb-sm">
            <div class="col">
              <q-input
                v-model="filter"
                dense
                outlined
                color="white"
                placeholder="Suchen..."
                class="search-field white-outline-input"
                input-class="text-white"
              >
                <template v-slot:append>
                  <q-icon name="search" color="white" />
                </template>
              </q-input>
            </div>
          </div>
        </template>
        <template v-slot:body-cell-plugged="props">
          <q-td :props="props">
            <ChargePointStateIcon :charge-point-id="props.row.id" />
          </q-td>
        </template>
      </q-table>
      <!-- ChargePointCard -->
      <q-dialog
        v-model="dialogVisible"
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
    </div>
  </div>
</template>

<style scoped>
.search-field {
  width: 100%;
  max-width: 18em;
}

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

<script setup lang="ts">
import { computed, ref } from 'vue';
import { useQuasar, Platform } from 'quasar';
import { useMqttStore } from 'src/stores/mqtt-store';
import BaseCarousel from 'src/components/BaseCarousel.vue';
import ChargePointCard from 'src/components/ChargePointCard.vue';
import ChargePointStateIcon from 'src/components/ChargePointStateIcon.vue';
import { useChargeModes } from 'src/composables/useChargeModes';
import { QTableColumn } from 'src/components/models/chargepoint-information-models';

const $q = useQuasar();
const mobile = computed(() => Platform.is.mobile);

const mqttStore = useMqttStore();
const selectedChargePointId = ref<number | null>(null);
const dialogVisible = ref(false);
const filter = ref('');

const chargePointIds = computed(() => mqttStore.chargePointIds);

const cardViewBreakpoint = computed(
  () => mqttStore.themeConfiguration?.card_view_breakpoint || 4,
);
const searchInputVisible = computed(
  () => mqttStore.themeConfiguration?.table_search_input_field,
);

const { chargeModes } = useChargeModes();

const rows = computed(() => {
  return chargePointIds.value.map((id) => {
    const chargePointName = mqttStore.chargePointName(id);
    const vehicleName =
      mqttStore.chargePointConnectedVehicleInfo(id).value?.name ||
      'Kein Fahrzeug';
    const plugState = mqttStore.chargePointPlugState(id) ? 'Ja' : 'Nein';
    const chargeModeValue =
      mqttStore.chargePointConnectedVehicleChargeMode(id).value;
    const chargeModeObj = chargeModes.find(
      (mode) => mode.value === chargeModeValue,
    );
    const chargeMode = chargeModeObj ? chargeModeObj.label : chargeModeValue;
    const soc = Math.round(
      mqttStore.chargePointConnectedVehicleSoc(id).value?.soc || 0,
    );
    const socDisplay = `${soc}%`;
    const power = mqttStore.chargePointPower(id, 'textValue');
    const energyCharged = mqttStore.chargePointEnergyChargedPlugged(
      id,
      'textValue',
    );
    return {
      id: id,
      name: chargePointName,
      vehicle: vehicleName,
      plugged: plugState,
      mode: chargeMode,
      soc: socDisplay,
      power: power,
      charged: energyCharged,
    };
  });
});

const columns: QTableColumn[] = [
  {
    name: 'name',
    label: 'Ladepunkt',
    field: 'name',
    sortable: true,
    align: 'left',
    headerStyle: 'font-weight: bold',
  },
  {
    name: 'vehicle',
    label: 'Fahrzeug',
    field: 'vehicle',
    sortable: true,
    align: 'left',
    headerStyle: 'font-weight: bold',
  },
  {
    name: 'plugged',
    label: 'Status',
    field: 'plugged',
    sortable: true,
    align: 'center',
    headerStyle: 'font-weight: bold',
  },
  {
    name: 'mode',
    label: 'Mode',
    field: 'mode',
    sortable: true,
    align: 'left',
    headerStyle: 'font-weight: bold',
  },
  {
    name: 'soc',
    label: 'Ladestand',
    field: 'soc',
    sortable: true,
    align: 'left',
    headerStyle: 'font-weight: bold',
  },
  {
    name: 'power',
    label: 'Leistung',
    field: 'power',
    sortable: true,
    align: 'left',
    headerStyle: 'font-weight: bold',
  },
  {
    name: 'charged',
    label: 'Geladen',
    field: 'charged',
    sortable: true,
    align: 'left',
    headerStyle: 'font-weight: bold',
  },
];
const columnsMobile = computed((): QTableColumn[] => {
  return [
    {
      name: 'name',
      label: 'Ladepunkt',
      field: 'name',
      sortable: true,
      align: 'left',
      headerStyle: 'font-weight: bold',
    },
    {
      name: 'vehicle',
      label: 'Fahrzeug',
      field: 'vehicle',
      sortable: true,
      align: 'left',
      headerStyle: 'font-weight: bold',
    },
    {
      name: 'plugged',
      label: 'Status',
      field: 'plugged',
      sortable: true,
      align: 'center',
      headerStyle: 'font-weight: bold',
    },
  ];
});

const onRowClick = (evt: Event, row: { id: number }) => {
  selectedChargePointId.value = row.id;
  dialogVisible.value = true;
};
</script>
