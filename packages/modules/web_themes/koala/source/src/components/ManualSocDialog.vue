<template>
  <q-dialog v-model="visible" @hide="reset" :persistent="dashboard && saving">
    <q-card>
      <q-card-section>
        <SettingsDialogHeader
          v-if="dashboard"
          :name="vehicleName"
          subtitle="SoC-Eingabe"
          :saving="saving"
          @close="visible = false"
          @apply="applyChanges"
        />
        <div v-else class="row">
          <div class="text-h6 q-mr-md">SoC-Eingabe {{ vehicleName }}</div>
          <q-space />
          <q-btn icon="close" flat round dense v-close-popup />
        </div>
      </q-card-section>
      <q-card-section class="q-py-none" :inert="saving || undefined">
        <div class="row justify-center items-center">
          <div class="col-6">
            <q-input
              v-model.number="socInputValue"
              type="text"
              inputmode="numeric"
              suffix="%"
              hide-spinner
              input-class="text-right"
            >
              <template v-slot:prepend>
                <q-btn
                  round
                  flat
                  dense
                  icon="remove"
                  @click="socInputValue--"
                />
              </template>
              <template v-slot:append>
                <q-btn round flat dense icon="add" @click="socInputValue++" />
              </template>
            </q-input>
          </div>
        </div>
        <div class="row justify-center items-center q-mt-md">
          <div class="col q-px-md">
            <q-slider
              v-model.number="socInputValue"
              :min="0"
              :max="100"
              :step="1"
              :markers="10"
              :marker-labels="socSliderMarker"
              color="primary"
            />
          </div>
        </div>
      </q-card-section>
      <q-card-actions v-if="!dashboard" align="center" class="q-mt-md">
        <q-btn label="Abbrechen" color="negative" v-close-popup />
        <q-btn
          label="Bestätigen"
          color="primary"
          v-close-popup
          @click="confirmChanges"
        />
      </q-card-actions>
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
import { useSettingsDialog } from 'src/composables/useSettingsDialog';
import SettingsDialogHeader from './SettingsDialogHeader.vue';
import SettingsDiscardDialog from './SettingsDiscardDialog.vue';
import { computed, ref } from 'vue';

const props = defineProps<{
  vehicleId: number | undefined;
  chargePointId?: number;
  socDialogVisible: boolean;
}>();

const emit = defineEmits<{
  'update:socDialogVisible': [value: boolean];
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
  () => props.socDialogVisible,
  (value) => emit('update:socDialogVisible', value),
  () => confirmChanges(),
);

const vehicleName = computed(() => {
  const vehicle = mqttStore.value.vehicleList.find(
    (v) => v.id === props.vehicleId,
  );
  return vehicle?.name || '';
});

const socValue = ref<number | undefined>(undefined);

const socInputValue = computed({
  get: () => {
    return (
      socValue.value ??
      mqttStore.value.vehicleSocManualValue(props.vehicleId).value ??
      0
    );
  },
  set: (newValue: number) => {
    // limit new value to 0-100
    socValue.value = Math.min(Math.max(0, newValue), 100);
  },
});

const socSliderMarker = {
  0: '0%',
  50: '50%',
  100: '100%',
};

const reset = () => {
  // Reset temporary soc value
  socValue.value = undefined;
};

const confirmChanges = () => {
  mqttStore.value.vehicleSocManualValue(
    props.vehicleId,
    props.chargePointId,
  ).value = socInputValue.value;
};
</script>
