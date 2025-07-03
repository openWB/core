<template>
  <SliderStandard
    title="Minimaler Dauerstrom"
    :min="-1"
    :max="16"
    :step="1"
    unit="A"
    :off-value-left="-1"
    :discrete-values="[-1, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16]"
    v-model="pvMinCurrent.value"
    class="q-mt-md"
  />

  <SliderStandard
    v-if="dcCharging"
    title="Minimaler DC-Dauerleistung"
    :min="0"
    :max="300"
    :step="1"
    unit="kW"
    v-model="pvMinDcPower.value"
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
  <div v-if="vehicleSocType !== undefined">
    <SliderStandard
      title="Mindest-SoC für das Fahrzeug"
      :min="0"
      :max="100"
      :step="5"
      unit="%"
      :off-value-left="0"
      v-model="pvMinSoc.value"
      class="q-mt-md"
    />
    <SliderStandard
      title="Mindest-SoC-Strom"
      :min="6"
      :max="32"
      unit="A"
      v-model="pvMinSocCurrent.value"
      class="q-mt-md"
    />

    <SliderStandard
      v-if="dcCharging"
      title="DC Mindest-SoC-Leistung"
      :min="0"
      :max="300"
      :step="1"
      unit="kW"
      v-model="pvMinDcMinSocPower.value"
      class="q-mt-md"
    />
    <div class="text-subtitle2 q-mt-sm q-mr-sm">Anzahl Phasen Mindest-SoC</div>
    <div class="row items-center justify-center q-ma-none q-pa-none no-wrap">
      <q-btn-group class="col">
        <q-btn
          v-for="option in phaseOptionsMinSoc"
          :key="option.value"
          :color="numPhasesMinSoc.value === option.value ? 'primary' : 'grey'"
          :label="option.label"
          size="sm"
          class="col"
          @click="numPhasesMinSoc.value = option.value"
        />
      </q-btn-group>
    </div>
  </div>

  <div class="row items-center justify-between q-ma-none q-pa-none no-wrap q-mt-md">
    <div class="text-subtitle2 q-mr-sm">Einspeisegrenze beachten</div>
    <div>
      <ToggleStandard dense v-model="feedInLimit.value" />
    </div>
  </div>
</template>

<script setup lang="ts">
import { useMqttStore } from 'src/stores/mqtt-store';
import SliderStandard from './SliderStandard.vue';
import ToggleStandard from './ToggleStandard.vue';
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
  { value: 0, label: 'Automatik' },
];

const phaseOptionsMinSoc = [
  { value: 1, label: '1' },
  { value: 3, label: 'Maximum' },
];

const pvMinCurrent = computed(() =>
  mqttStore.chargePointConnectedVehiclePvChargeMinCurrent(props.chargePointId),
);

const dcCharging = computed(() => mqttStore.dcChargingEnabled);

const pvMinDcPower = computed(() =>
  mqttStore.chargePointConnectedVehiclePvDcChargePower(props.chargePointId),
);

const pvMinDcMinSocPower = computed(() =>
  mqttStore.chargePointConnectedVehiclePvDcMinSocPower(props.chargePointId),
);

const numPhases = computed(() =>
  mqttStore.chargePointConnectedVehiclePvChargePhases(props.chargePointId),
);

const numPhasesMinSoc = computed(() =>
  mqttStore.chargePointConnectedVehiclePvChargePhasesMinSoc(
    props.chargePointId,
  ),
);

const pvMinSoc = computed(() =>
  mqttStore.chargePointConnectedVehiclePvChargeMinSoc(props.chargePointId),
);

const pvMinSocCurrent = computed(() =>
  mqttStore.chargePointConnectedVehiclePvChargeMinSocCurrent(
    props.chargePointId,
  ),
);

const limitMode = computed(() =>
  mqttStore.chargePointConnectedVehiclePvChargeLimit(props.chargePointId),
);

const limitSoC = computed(() =>
  mqttStore.chargePointConnectedVehiclePvChargeLimitSoC(props.chargePointId),
);

const limitEnergy = computed(() =>
  mqttStore.chargePointConnectedVehiclePvChargeLimitEnergy(props.chargePointId),
);

const feedInLimit = computed(() =>
  mqttStore.chargePointConnectedVehiclePvChargeFeedInLimit(props.chargePointId),
);
</script>
