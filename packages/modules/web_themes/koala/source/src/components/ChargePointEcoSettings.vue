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

  <SliderStandard
    v-if="dcCharging"
    title="Minimaler Dauerleistung unter der Preisgrenze"
    :min="4"
    :max="300"
    :step="1"
    unit="kW"
    v-model="dcPower.value"
    class="q-mt-md"
  />

  <div class="text-subtitle2 q-mt-sm q-mr-sm">Anzahl Phasen bei Überschuss</div>
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
  <div v-if="etConfigured">
    <div class="text-subtitle2 q-my-sm">
      Preisgrenze für strompreisbasiertes Laden
    </div>
    <div class="row no-wrap items-center justify-between q-mb-xs q-gutter-x-xs">
      <div class="col-auto">
        <q-btn
          v-if="maxPrice.value"
          class="col-auto q-mr-xs"
          label="-1,00"
          color="grey"
          size="sm"
          dense
          @click="maxPrice.value = maxPrice.value - 1"
        />
        <q-btn
          v-if="maxPrice.value"
          class="col-auto q-mr-xs"
          label="-0,10"
          color="grey"
          size="sm"
          dense
          @click="maxPrice.value = maxPrice.value - 0.1"
        />
        <q-btn
          v-if="maxPrice.value"
          class="col-auto"
          label="-0,01"
          color="grey"
          size="sm"
          dense
          @click="maxPrice.value = maxPrice.value - 0.01"
        />
      </div>
      <div class="col-auto q-mx-sm">
        {{
          maxPrice.value?.toLocaleString(undefined, {
            minimumFractionDigits: 2,
            maximumFractionDigits: 2,
          }) + ' ct/kWh'
        }}
      </div>
      <div class="col-auto">
        <q-btn
          v-if="maxPrice.value"
          class="col-auto q-mr-xs"
          label="+0,01"
          color="grey"
          size="sm"
          dense
          @click="maxPrice.value = maxPrice.value + 0.01"
        />
        <q-btn
          v-if="maxPrice.value"
          class="col-auto q-mr-xs"
          label="+0,10"
          color="grey"
          size="sm"
          dense
          @click="maxPrice.value = maxPrice.value + 0.1"
        />
        <q-btn
          v-if="maxPrice.value"
          class="col-auto"
          label="+1,00"
          color="grey"
          size="sm"
          dense
          @click="maxPrice.value = maxPrice.value + 1"
        />
      </div>
    </div>
    <q-field filled class="q-mt-sm">
      <ElectricityTariffChart
        :modelValue="maxPrice.value"
        @update:modelValue="maxPrice.value = $event"
      />
    </q-field>
  </div>
</template>

<script setup lang="ts">
import { useMqttStore } from 'src/stores/mqtt-store';
import SliderStandard from './SliderStandard.vue';
import ElectricityTariffChart from './ElectricityTariffChart.vue';
import { computed } from 'vue';

const props = defineProps<{
  chargePointId: number;
}>();

const mqttStore = useMqttStore();

const limitModes = computed(() => {
  let modes = [
    { value: 'none', label: 'keine', color: 'primary' },
    { value: 'soc', label: 'EV-SoC', color: 'primary' },
    { value: 'amount', label: 'Energie', color: 'primary' },
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

const current = computed(() =>
  mqttStore.chargePointConnectedVehicleEcoChargeCurrent(props.chargePointId),
);

const dcCharging = computed(() => mqttStore.dcChargingEnabled);

const dcPower = computed(() =>
  mqttStore.chargePointConnectedVehicleEcoChargeDcPower(props.chargePointId),
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

const etConfigured = computed(() => mqttStore.etProviderConfigured);

const maxPrice = computed(() =>
  mqttStore.chargePointConnectedVehicleEcoChargeMaxPrice(props.chargePointId),
);
</script>
