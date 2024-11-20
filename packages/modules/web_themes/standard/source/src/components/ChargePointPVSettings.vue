<template>
  <SliderStandard
    title="Minimaler Dauerstrom"
    :min="0"
    :max="16"
    unit="A"
    v-model="pvMinCurrent.value"
    class="q-mt-md"
  />

  <SliderStandard
    title="Mindest-SoC für das Fahrzeug"
    :min="0"
    :max="95"
    :step="5"
    unit="%"
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
    title="SoC-Limit für das Fahrzeug"
    :min="0"
    :max="100"
    :step="5"
    unit="%"
    v-model="pvMaxSocLimit.value"
    class="q-mt-md"
  />

  <div class="row items-center q-ma-none q-pa-none no-wrap">
    <div class="text-subtitle2 q-mr-sm">Einspeisegrenze beachten</div>
    <div>
      <ToggleStandard v-model="feedInLimit.value" />
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

const pvMinCurrent = computed(() =>
  mqttStore.chargePointConnectedVehiclePVChargeMinCurrent(props.chargePointId),
);

const pvMinSoc = computed(() =>
  mqttStore.chargePointConnectedVehiclePVChargeMinSoc(props.chargePointId),
);

const pvMinSocCurrent = computed(() =>
  mqttStore.chargePointConnectedVehiclePVChargeMinSocCurrent(
    props.chargePointId,
  ),
);

const pvMaxSocLimit = computed(() =>
  mqttStore.chargePointConnectedVehiclePVChargeMaxSoc(props.chargePointId),
);

const feedInLimit = computed(() =>
  mqttStore.chargePointConnectedVehiclePVChargeFeedInLimit(props.chargePointId),
);
</script>
