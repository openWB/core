<template>
  <q-dialog
    v-model="visible"
    :backdrop-filter="isSmallScreen ? '' : 'blur(4px)'"
  >
    <q-card>
      <q-card-section>
      <div class="row nowrap q-mb-sm">
        <div class="text-h6">Begrenzung</div>
        <q-space />
        <q-btn icon="close" flat round dense v-close-popup />
      </div>
      <q-separator class="q-mt-sm q-mb-sm" />

        <div
          class="row items-center justify-center q-ma-none q-pa-none no-wrap"
        >
          <q-btn-group class="col">
            <q-btn
              v-for="mode in limitModes"
              :key="mode.value"
              :color="limitMode.value === mode.value ? 'primary' : 'grey'"
              :label="mode.label"
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
          unit="%"
          v-model="limitSoC.value"
          class="q-mt-md"
        />
        <SliderStandard
          v-if="limitMode.value === 'amount'"
          title="Energie-Limit"
          :min="1"
          :max="50"
          unit="kWh"
          v-model="limitEnergy.value"
          class="q-mt-md"
        />
      </q-card-section>
    </q-card>
  </q-dialog>
</template>

<script setup lang="ts">
import { Screen, QDialog } from 'quasar';
import { useMqttStore } from 'src/stores/mqtt-store';
import SliderStandard from './SliderStandard.vue';
import { computed, ref, watch } from 'vue';

const props = defineProps<{
  chargePointId: number;
  modelValue: boolean;
  energyTargetEnabled: boolean;
}>();

const emit = defineEmits<{
  'update:model-value': [value: boolean];
}>();

const mqttStore = useMqttStore();

const isSmallScreen = computed(() => Screen.lt.sm);
const tempValue = ref<boolean>(props.modelValue);

  const baseLimitModes = [
  { value: 'none', label: 'keine' },
  { value: 'soc', label: 'EV-SoC' },
  { value: 'amount', label: 'Energie' },
]

const limitModes = computed(() => {
  return baseLimitModes.filter((mode) => {
    // If vehicle has no SoC module → remove soc
    if (!vehicleSocType.value && mode.value === 'soc') {
      return false
    }
    return true
  })
})

const vehicleSocType = computed(() =>
  mqttStore.chargePointConnectedVehicleSocType(props.chargePointId),
)?.value;

const limitMode = computed(() =>
  mqttStore.chargePointConnectedVehicleInstantChargeLimit(props.chargePointId),
);

const limitSoC = computed(() =>
  mqttStore.chargePointConnectedVehicleInstantChargeLimitSoC(
    props.chargePointId,
  ),
);

const limitEnergy = computed(() =>
  mqttStore.chargePointConnectedVehicleInstantChargeLimitEnergy(
    props.chargePointId,
  ),
);

const visible = computed({
  get: () => tempValue.value,
  set: (value) => {
    tempValue.value = value;
    emit('update:model-value', value );
  },
});

watch(
  () => props.modelValue,
  (value) => {
    tempValue.value = value;
  },
);
</script>

<style scoped>
.q-btn-group .q-btn {
  min-width: 100px !important;
}

body.mobile .q-btn-group .q-btn {
  padding: 4px 8px;
  font-size: 12px !important;
  min-height: 30px;
}
</style>
