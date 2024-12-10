<template>
  <SliderStandard
    title="Stromstärke"
    :min="6"
    :max="32"
    unit="A"
    v-model="instantChargeCurrent.value"
    class="q-mt-sm"
  />
  <!-- <SliderQuasar class="q-mt-sm" :readonly="false" /> -->
  <div class="text-subtitle2 q-mr-sm">Begrenzung</div>
  <div class="row items-center justify-center q-ma-none q-pa-none no-wrap">
    <q-btn-group class="q-mt-md col">
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
  { value: 'none', label: 'keine', color: 'primary' },
  { value: 'soc', label: 'EV-SoC', color: 'primary' },
  { value: 'amount', label: 'Energiemenge', color: 'primary' },
];

const instantChargeCurrent = computed(() =>
  mqttStore.chargePointConnectedVehicleInstantChargeCurrent(
    props.chargePointId,
  ),
);

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
