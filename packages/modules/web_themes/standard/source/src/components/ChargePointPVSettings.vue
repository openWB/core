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
    class="q-mt-md q-ml-sm"
  />

  <SliderStandard
    title="Mindest-SoC für das Fahrzeug"
    :min="0"
    :max="100"
    :step="5"
    unit="%"
    :off-value-left="0"
    v-model="pvMinSoc.value"
    class="q-mt-md q-ml-sm"
  />

  <SliderStandard
    title="Mindest-SoC-Strom"
    :min="6"
    :max="32"
    unit="A"
    v-model="pvMinSocCurrent.value"
    class="q-mt-md q-ml-sm"
  />

  <SliderStandard
    title="SoC-Limit für das Fahrzeug"
    :min="0"
    :max="101"
    :step="1"
    unit="%"
    :discrete-values="[
      0, 5, 10, 15, 20, 25, 30, 35, 40, 45, 50, 55, 60, 65, 70, 75, 80, 85, 90,
      95, 100, 101,
    ]"
    :off-value-right="101"
    v-model="pvMaxSocLimit.value"
    class="q-mt-md q-ml-sm"
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
