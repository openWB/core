<template>
  <SliderStandard
    v-if="acChargingEnabled"
    title="Minimaler Dauerstrom"
    :min="0"
    :max="16"
    :step="1"
    unit="A"
    :off-value-left="0"
    :discrete-values="[0, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16]"
    v-model="pvMinCurrent.value"
    class="q-mt-md"
  />

  <SliderStandard
    v-if="dcChargingEnabled"
    title="Minimaler DC-Dauerleistung"
    :min="0"
    :max="300"
    :step="1"
    unit="kW"
    v-model="pvMinDcPower.value"
    class="q-mt-md"
  />

  <div v-if="acChargingEnabled">
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
  </div>
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
      v-if="acChargingEnabled"
      title="Mindest-SoC-Strom"
      :min="6"
      :max="32"
      unit="A"
      v-model="pvMinSocCurrent.value"
      class="q-mt-md"
    />

    <SliderStandard
      v-if="dcChargingEnabled"
      title="DC Mindest-SoC-Leistung"
      :min="0"
      :max="300"
      :step="1"
      unit="kW"
      v-model="pvMinDcMinSocPower.value"
      class="q-mt-md"
    />
    <div v-if="acChargingEnabled">
      <div class="text-subtitle2 q-mt-sm q-mr-sm">
        Anzahl Phasen Mindest-SoC
      </div>
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
  </div>

  <div
    class="row items-center justify-between q-ma-none q-pa-none no-wrap q-mt-md"
  >
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

const dcChargingEnabled = computed(
  () => mqttStore.chargePointChargeType(props.chargePointId).value === 'DC',
);

const acChargingEnabled = computed(
  () => mqttStore.chargePointChargeType(props.chargePointId).value === 'AC',
);

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

const feedInLimit = computed(() =>
  mqttStore.chargePointConnectedVehiclePvChargeFeedInLimit(props.chargePointId),
);
</script>
