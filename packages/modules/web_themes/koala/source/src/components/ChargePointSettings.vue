<template>
  <q-dialog
    v-model="visible"
    :maximized="isSmallScreen"
    :backdrop-filter="isSmallScreen ? '' : 'blur(4px)'"
    :persistent="dashboard && saving"
  >
    <q-card :class="{ 'dashboard-charge-point-settings': dashboard }">
      <q-card-section>
        <SettingsDialogHeader
          v-if="dashboard"
          :name="name"
          :saving="saving"
          @close="visible = false"
          @apply="applyChanges"
        />
        <div v-else class="row no-wrap">
          <div class="text-h6 q-pr-sm">Einstellungen:</div>
          <div class="text-h6 ellipsis" :title="name">{{ name }}</div>
          <q-space />
          <q-btn icon="close" flat round dense v-close-popup />
        </div>
      </q-card-section>
      <q-separator />
      <q-card-section :inert="saving || undefined">
        <div class="row items-center justify-between">
          <div class="text-subtitle2">Ladepunkt sperren</div>
          <ChargePointLock :charge-point-id="props.chargePointId" dense />
        </div>
        <q-separator class="q-mt-sm" />
        <div class="row items-center q-mt-sm">
          <div class="col-auto text-subtitle2 q-mr-sm">Fahrzeug</div>
          <div class="col">
            <ChargePointVehicleSelect
              class="full-width"
              :charge-point-id="props.chargePointId"
              :readonly="false"
            />
          </div>
        </div>
        <q-separator class="q-mt-sm" />
        <div class="row items-center no-wrap">
          <ChargePointModeButtons :charge-point-id="props.chargePointId" />
        </div>
        <!-- ///////////////// Instant charge settings /////////////////// -->
        <div v-if="chargeMode.value === 'instant_charging'">
          <ChargePointInstantSettings :charge-point-id="props.chargePointId" />
        </div>
        <!-- ///////////////// Pv charge settings /////////////////// -->
        <div v-if="chargeMode.value === 'pv_charging'">
          <ChargePointPvSettings :charge-point-id="props.chargePointId" />
        </div>
        <!-- ///////////////// Eco charge settings /////////////////// -->
        <div v-if="chargeMode.value === 'eco_charging'">
          <ChargePointEcoSettings :charge-point-id="props.chargePointId" />
        </div>
        <!-- /////////////////  scheduled charging settings /////////////////// -->
        <div v-if="chargeMode.value === 'scheduled_charging'">
          <ChargePointScheduledSettings
            :charge-point-id="props.chargePointId"
          />
        </div>
        <!-- /////////////////  time charging settings /////////////////// -->
        <div v-if="chargeMode.value !== 'stop'">
          <q-separator class="q-my-sm" />
          <ChargePointTimeChargingSettings
            :charge-point-id="props.chargePointId"
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
import { computed } from 'vue';
import { useSettingsDialog } from 'src/composables/useSettingsDialog';
import SettingsDialogHeader from './SettingsDialogHeader.vue';
import SettingsDiscardDialog from './SettingsDiscardDialog.vue';
import ChargePointInstantSettings from './ChargePointInstantSettings.vue';
import ChargePointPvSettings from './ChargePointPvSettings.vue';
import ChargePointEcoSettings from './ChargePointEcoSettings.vue';
import ChargePointScheduledSettings from './ChargePointScheduledSettings.vue';
import ChargePointTimeChargingSettings from './ChargePointTimeChargingSettings.vue';
import ChargePointLock from './ChargePointLock.vue';
import ChargePointModeButtons from './ChargePointModeButtons.vue';
import ChargePointVehicleSelect from './ChargePointVehicleSelect.vue';

const props = defineProps<{
  chargePointId: number;
  modelValue: boolean;
}>();

const emit = defineEmits<{
  'update:model-value': [value: boolean];
}>();

const isSmallScreen = computed(() => Screen.lt.sm);

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

const chargeMode = computed(() =>
  mqttStore.value.chargePointConnectedVehicleChargeMode(props.chargePointId),
);
</script>

<style scoped>
.dashboard-charge-point-settings {
  width: 680px;
  min-width: min(600px, calc(100vw - 48px));
  max-width: calc(100vw - 48px);
}
@media (max-width: 599px) {
  .dashboard-charge-point-settings {
    width: 100%;
    min-width: 0;
    max-width: 100%;
  }
}
</style>
