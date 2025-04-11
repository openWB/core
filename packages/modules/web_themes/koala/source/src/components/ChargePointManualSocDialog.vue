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
        <div class="row justify-center items-center q-ma-none q-pa-none">
          <div class="col-6 col-sm-8 col-md-6">
            <q-input
              v-model.number="socInputValue"
              type="text"
              inputmode="numeric"
              class="text-center"
              suffix="%"
              hide-spinner
            >
              <template v-slot:prepend>
                <q-btn round flat dense icon="remove" @click="decrementSoc" />
              </template>
              <template v-slot:append>
                <q-btn round flat dense icon="add" @click="incrementSoc" />
              </template>
            </q-input>
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
import { computed, ref, watch, onMounted } from 'vue';

const mqttStore = useMqttStore();

const props = defineProps<{
  chargePointId: number;
  socDialogVisible: boolean;
}>();

const emit = defineEmits<{
  'update:socDialogVisible': [value: boolean];
}>();

const visible = computed({
  get: () => props.socDialogVisible,
  set: (value) => {
    emit('update:socDialogVisible', value);
    if (value) getManualSocValue();
  },
});

const vehicleName = computed(() => {
  return mqttStore.chargePointConnectedVehicleInfo(props.chargePointId).value
    ?.name;
});

const socInputValue = ref<number>(0);

const getManualSocValue = async () => {
  const vehicleInfo = mqttStore.chargePointConnectedVehicleInfo(props.chargePointId).value;
  const vehicleId = vehicleInfo?.id;
  const socTopic = `openWB/vehicle/${vehicleId}/soc_module/calculated_soc_state`;
  mqttStore.subscribe(socTopic);
  await new Promise(resolve => setTimeout(resolve, 100));
  const storeValue = mqttStore.chargePointConnectedVehicleSocManual(props.chargePointId).value ?? 0;
  socInputValue.value = storeValue;
};

onMounted(() => {
  getManualSocValue();
});

watch(
  () => visible.value,
  (isOpen) => {
    if (isOpen) {
      getManualSocValue();
    }
  },
);

const incrementSoc = () => {
  if (socInputValue.value < 100) {
    socInputValue.value++;
  }
};

const decrementSoc = () => {
  if (socInputValue.value > 0) {
    socInputValue.value--;
  }
};

const confirmChanges = () => {
  mqttStore.chargePointConnectedVehicleSocManual(props.chargePointId).value =
    socInputValue.value;
};

const cancelChanges = () => {
  // Reset to store value
  getManualSocValue();
};
</script>
