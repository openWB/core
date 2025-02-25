<template>
  <SliderStandard
    title="Minimaler Dauerstrom unter der Preisgrenze"
    :min="6"
    :max="16"
    :step="1"
    unit="A"
    v-model="current.value"
    class="q-mt-md"
  />

  <div class="text-subtitle2 q-mt-sm q-mr-sm">Anzahl Phasen</div>
  <div class="row items-center justify-center q-ma-none q-pa-none no-wrap">
    <q-btn-group class="col">
      <q-btn
        v-for="option in phaseOptions"
        :key="option.value"
        :color="numPhases.value === option.value ? 'primary' : 'grey'"
        :label="option.label"
        size="sm"
        class="col"
        @click="numPhases.value = option.value"
      />
    </q-btn-group>
  </div>

  <div class="text-subtitle2 q-mt-sm q-mr-sm">Begrenzung</div>
  <div class="row items-center justify-center q-ma-none q-pa-none no-wrap">
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
  <div class="text-subtitle2 q-mt-sm q-mr-sm">
    Preisgrenze für strompreisbasiertes Laden
  </div>
  <div class="row items-center justify-center q-ma-none q-pa-none no-wrap">
    <q-btn-group class="col">
      <q-btn
        color="grey"
        :label="
          maxPrice.value?.toLocaleString(undefined, {
            minimumFractionDigits: 2,
            maximumFractionDigits: 2,
          }) + ' ct/kWh'
        "
        size="sm"
        class="col"
        :no-caps="true"
        @click="console.log('maxPrice clicked', maxPrice.value)"
      />
    </q-btn-group>
  </div>
</template>

<script setup lang="ts">
import { useMqttStore } from 'src/stores/mqtt-store';
import SliderStandard from './SliderStandard.vue';
import { computed } from 'vue';

const props = defineProps<{
  chargePointId: number;
}>();

const mqttStore = useMqttStore();

const limitModes = [
  { value: 'none', label: 'keine', color: 'primary' },
  { value: 'soc', label: 'EV-SoC', color: 'primary' },
  { value: 'amount', label: 'Energiemenge', color: 'primary' },
];

const phaseOptions = [
  { value: 1, label: '1' },
  { value: 3, label: 'Maximum' },
  { value: 0, label: 'Automatik' },
];

const current = computed(() =>
  mqttStore.chargePointConnectedVehicleEcoChargeCurrent(props.chargePointId),
);

const numPhases = computed(() =>
  mqttStore.chargePointConnectedVehicleEcoChargePhases(props.chargePointId),
);

const limitMode = computed(() =>
  mqttStore.chargePointConnectedVehicleEcoChargeLimit(props.chargePointId),
);

const limitSoC = computed(() =>
  mqttStore.chargePointConnectedVehicleEcoChargeLimitSoC(props.chargePointId),
);

const limitEnergy = computed(() =>
  mqttStore.chargePointConnectedVehicleEcoChargeLimitEnergy(
    props.chargePointId,
  ),
);

const maxPrice = computed(() =>
  mqttStore.chargePointConnectedVehicleEcoChargeMaxPrice(props.chargePointId),
);
</script>
