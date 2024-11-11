<template>
  <div class="row items-center justify-center q-ma-none q-pa-none no-wrap">
    <q-btn-group push rounded class="q-mt-md col">
      <q-btn
        v-for="mode in limitModes"
        :key="mode.value"
        :flat="limitMode.value !== mode.value"
        :outline="limitMode.value === mode.value"
        :glossy="limitMode.value === mode.value"
        :label="mode.label"
        :color="mode.color"
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
    v-model="instantSoC.value"
    class="q-mt-md"
  />
  <SliderStandard
    v-if="limitMode.value === 'amount'"
    title="Energie-Limit"
    :min="1"
    :max="50"
    unit="kWh"
    v-model="instantEnergy.value"
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

const limitModes = [
  { value: 'none', label: 'keine', color: 'secondary' },
  { value: 'soc', label: 'EV-SoC', color: 'secondary' },
  { value: 'amount', label: 'Energiemenge', color: 'secondary' },
];

const limitMode = computed(() =>
  mqttStore.chargePointConnectedVehicleInstantChargeLimit(props.chargePointId),
);

const instantSoC = computed(() =>
  mqttStore.chargePointConnectedVehicleInstantChargeLimitSoC(
    props.chargePointId,
  ),
);

const instantEnergy = computed(() =>
  mqttStore.chargePointConnectedVehicleInstantChargeEnergieLimit(
    props.chargePointId,
  ),
);
</script>
