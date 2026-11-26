<template>
  <q-dialog
    v-model="visible"
    :backdrop-filter="isSmallScreen ? '' : 'blur(4px)'"
    :persistent="dashboard && saving"
  >
    <q-card class="card-width">
      <q-card-section>
        <SettingsDialogHeader
          v-if="dashboard"
          :name="name"
          subtitle="Begrenzung"
          :saving="saving"
          @close="visible = false"
          @apply="applyChanges"
        />
        <div v-else class="row nowrap q-mb-sm">
          <div class="text-h6">Begrenzung</div>
          <q-space />
          <q-btn icon="close" flat round dense v-close-popup />
        </div>
        <q-separator class="q-mt-sm q-mb-sm" />
        <div :inert="saving || undefined">
          <div v-if="isSmallScreen" class="row q-pt-md full-width">
            <q-btn-dropdown
              class="col"
              transition-show="scale"
              transition-hide="scale"
              transition-duration="500"
              color="primary"
              :label="currentLimitModeLabel"
              size="md"
              dropdown-icon="none"
              cover
              push
            >
              <q-list>
                <template v-for="(mode, index) in limitModes" :key="mode.value">
                  <q-item
                    clickable
                    v-close-popup
                    @click="limitMode.value = mode.value"
                    :active="limitMode.value === mode.value"
                    :disable="mode.value === 'soc' && !vehicleSocType"
                    active-class="bg-primary text-white"
                  >
                    <q-item-section class="text-center text-weight-bold">
                      <q-item-label>{{
                        mode.label.toLocaleUpperCase()
                      }}</q-item-label>
                    </q-item-section>
                  </q-item>
                  <q-separator v-if="index < limitModes.length - 1" />
                </template>
              </q-list>
            </q-btn-dropdown>
          </div>
          <div
            v-else
            class="row items-center justify-center q-ma-none q-pa-none no-wrap"
          >
            <q-btn-group class="col" outline>
              <q-btn
                v-for="mode in limitModes"
                :key="mode.value"
                :color="limitMode.value === mode.value ? 'primary' : 'grey'"
                :label="mode.label"
                :disable="mode.value === 'soc' && !vehicleSocType"
                :outline="mode.value !== limitMode.value"
                size="sm"
                class="col"
                @click="limitMode.value = mode.value"
              />
            </q-btn-group>
          </div>
          <SliderStandard
            v-if="limitMode.value === 'soc'"
            title="SoC-Limit für das Fahrzeug"
            :min="5"
            :max="100"
            :step="5"
            color="light-green-14"
            :track-size="'1em'"
            thumb-size="2.3em"
            thumb-color="light-green-14"
            unit="%"
            v-model="limitSoC.value"
            class="q-mt-md"
          />
          <SliderStandard
            v-if="limitMode.value === 'amount'"
            title="Energie-Limit"
            :min="1"
            :max="50"
            color="green-7"
            :track-size="'1em'"
            thumb-size="2.3em"
            thumb-color="green-7"
            unit="kWh"
            v-model="limitEnergy.value"
            class="q-mt-md"
          />
        </div>
      </q-card-section>
      <SettingsDiscardDialog
        :model-value="confirmClose"
        :saving="saving"
        @discard="discardChanges"
        @apply="applyChanges"
      />
    </q-card>
  </q-dialog>
</template>

<script setup lang="ts">
import { Screen, QDialog } from 'quasar';
import { useSettingsDialog } from 'src/composables/useSettingsDialog';
import SettingsDialogHeader from './SettingsDialogHeader.vue';
import SettingsDiscardDialog from './SettingsDiscardDialog.vue';
import SliderStandard from './SliderStandard.vue';
import { computed, ref } from 'vue';

const props = defineProps<{
  chargePointId: number;
  modelValue: boolean;
}>();

const emit = defineEmits<{
  'update:model-value': [value: boolean];
}>();

const {
  dashboard,
  mqttStore,
  visible,
  saving,
  confirmClose,
  discardChanges,
  applyChanges,
} = useSettingsDialog(
  () => props.modelValue,
  (value) => emit('update:model-value', value),
);
const name = computed(() =>
  mqttStore.value.chargePointName(props.chargePointId),
);

const isSmallScreen = computed(() => Screen.lt.sm);

const limitModes = [
  { value: 'none', label: 'keine' },
  { value: 'soc', label: 'EV-SoC' },
  { value: 'amount', label: 'Energie' },
];

const vehicleSocType = computed(() =>
  mqttStore.value.chargePointConnectedVehicleSocType(props.chargePointId).value,
);

const chargeMode = computed(
  () =>
    mqttStore.value.chargePointConnectedVehicleChargeMode(props.chargePointId)
      ?.value,
);

const activeChargeLimitConfig = computed(() => {
  switch (chargeMode.value) {
    case 'instant_charging':
      return {
        mode: mqttStore.value.chargePointConnectedVehicleInstantChargeLimit(
          props.chargePointId,
        ),
        soc: mqttStore.value.chargePointConnectedVehicleInstantChargeLimitSoC(
          props.chargePointId,
        ),
        energy:
          mqttStore.value.chargePointConnectedVehicleInstantChargeLimitEnergy(
            props.chargePointId,
          ),
      };
    case 'pv_charging':
      return {
        mode: mqttStore.value.chargePointConnectedVehiclePvChargeLimit(
          props.chargePointId,
        ),
        soc: mqttStore.value.chargePointConnectedVehiclePvChargeLimitSoC(
          props.chargePointId,
        ),
        energy: mqttStore.value.chargePointConnectedVehiclePvChargeLimitEnergy(
          props.chargePointId,
        ),
      };
    case 'eco_charging':
      return {
        mode: mqttStore.value.chargePointConnectedVehicleEcoChargeLimit(
          props.chargePointId,
        ),
        soc: mqttStore.value.chargePointConnectedVehicleEcoChargeLimitSoC(
          props.chargePointId,
        ),
        energy: mqttStore.value.chargePointConnectedVehicleEcoChargeLimitEnergy(
          props.chargePointId,
        ),
      };
    default:
      return {
        mode: ref('none'),
        soc: ref(0),
        energy: ref(0),
      };
  }
});

const limitMode = computed(() => activeChargeLimitConfig.value.mode);
const limitSoC = computed(() => activeChargeLimitConfig.value.soc);
const limitEnergy = computed(() => activeChargeLimitConfig.value.energy);

const currentLimitModeLabel = computed(
  () => limitModes.find((mode) => mode.value === limitMode.value.value)?.label,
);
</script>

<style scoped>
.card-width {
  width: 25em;
}
.q-btn-group .q-btn {
  min-width: 100px !important;
}

body.mobile .q-btn-group .q-btn {
  padding: 4px 8px;
  font-size: 12px !important;
  min-height: 30px;
}

:deep(.q-btn-dropdown__arrow-container) {
  width: 0;
  padding: 0;
  margin: 0;
}
</style>
