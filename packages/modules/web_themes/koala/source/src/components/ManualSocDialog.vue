<template>
  <q-dialog v-model="visible">
    <q-card>
      <q-card-section>
        <div class="row">
          <div class="text-h6 q-mr-md">SoC-Eingabe {{ vehicleName }}</div>
          <q-space />
          <q-btn icon="close" flat round dense v-close-popup />
        </div>
      </q-card-section>
      <q-card-section class="q-py-none">
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
      <q-card-actions align="center" class="q-mt-md">
        <q-btn
          label="Abbrechen"
          color="negative"
          v-close-popup
          @click="cancelChanges"
        />
        <q-btn
          label="Bestätigen"
          color="primary"
          v-close-popup
          @click="confirmChanges"
        />
      </q-card-actions>
    </q-card>
  </q-dialog>
</template>

<script setup lang="ts">
import { useMqttStore } from 'src/stores/mqtt-store';
import { computed, ref } from 'vue';

const mqttStore = useMqttStore();

const props = defineProps<{
  vehicleId: number | undefined;
  chargePointId?: number;
  socDialogVisible: boolean;
}>();

const emit = defineEmits<{
  'update:socDialogVisible': [value: boolean];
}>();

const vehicleName = computed(() => {
  const vehicle = mqttStore.vehicleList.find((v) => v.id === props.vehicleId);
  return vehicle?.name || '';
});

const visible = computed({
  get: () => props.socDialogVisible,
  set: (value) => {
    emit('update:socDialogVisible', value);
  },
});

const socValue = ref<number | undefined>(undefined);

const socInputValue = computed({
  get: () => {
    return (
      socValue.value ??
      mqttStore.vehicleSocManualValue(props.vehicleId).value ??
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

const confirmChanges = () => {
  mqttStore.vehicleSocManualValue(props.vehicleId, props.chargePointId).value =
    socInputValue.value;
};

const cancelChanges = () => {
  // Reset temporary soc value
  socValue.value = undefined;
};
</script>
