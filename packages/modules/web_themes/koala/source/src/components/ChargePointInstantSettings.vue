<template>
  <SliderStandard
    title="Stromstärke"
    :min="6"
    :max="32"
    unit="A"
    v-model="instantChargeCurrent.value"
    class="q-mt-sm"
  />
  <SliderStandard
    v-if="dcCharging"
    title="DC-Sollleistung"
    :min="4"
    :max="300"
    unit="kW"
    v-model="instantChargeCurrentDc.value"
    class="q-mt-sm"
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
</template>

<script setup lang="ts">
import { useMqttStore } from 'src/stores/mqtt-store';
import SliderStandard from './SliderStandard.vue';
import { computed } from 'vue';

const props = defineProps<{
  chargePointId: number;
}>();

const mqttStore = useMqttStore();

const limitModes = computed(() => {
  let modes = [
    { value: 'none', label: 'keine', color: 'primary' },
    { value: 'soc', label: 'EV-SoC', color: 'primary' },
    { value: 'amount', label: 'Energiemenge', color: 'primary' },
  ];
  if (vehicleSocType.value === undefined) {
    modes = modes.filter((mode) => mode.value !== 'soc');
  }
  return modes;
});

const vehicleSocType = computed(() =>
  mqttStore.chargePointConnectedVehicleSocType(props.chargePointId),
)?.value;

const phaseOptions = [
  { value: 1, label: '1' },
  { value: 3, label: 'Maximum' },
];

const instantChargeCurrent = computed(() =>
  mqttStore.chargePointConnectedVehicleInstantChargeCurrent(
    props.chargePointId,
  ),
);

const dcCharging = computed(() => mqttStore.dcChargingEnabled);

const instantChargeCurrentDc = computed(() => {
  return mqttStore.chargePointConnectedVehicleInstantDcChargePower(
    props.chargePointId,
  );
});

const numPhases = computed(() =>
  mqttStore.chargePointConnectedVehicleInstantChargePhases(props.chargePointId),
);

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
</script>
