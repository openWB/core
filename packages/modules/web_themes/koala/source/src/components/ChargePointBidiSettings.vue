<template>
  <SliderStandard
    title="Minimaler Entlade-SoC"
    :min="5"
    :max="100"
    :step="5"
    unit="%"
    v-model="minDischargeSoC.value"
    class="q-mt-md"
  />
  <SliderStandard
    title="Stromstärke"
    :min="6"
    :max="32"
    :step="1"
    unit="A"
    v-model="current.value"
    class="q-mt-md"
  />
  <div class="text-subtitle2 q-mr-sm q-mt-md">Bidi-Plan:</div>
  <div class="column q-mt-sm">
    <PlanDetailsDisplay
      :frequency="plan?.frequency.selected"
      :time="plan?.time"
      :limitType="'soc'"
      :socScheduled="plan?.limit.soc_scheduled"
      :date="plan?.frequency.once"
      :weeklyDays="plan?.frequency.weekly"
      :limitIcon="'battery_full'"
      :etActive="planEtActive"
    />
  </div>
</template>

<script setup lang="ts">
import { useMqttStore } from 'src/stores/mqtt-store';
import { computed } from 'vue';
import PlanDetailsDisplay from './PlanDetailsDisplay.vue';
import SliderStandard from './SliderStandard.vue';

const props = defineProps<{
  chargePointId: number;
}>();

const mqttStore = useMqttStore();

const plan = computed(() =>
  mqttStore.chargePointConnectedVehicleBidiChargePlan(props.chargePointId),
);

const minDischargeSoC = computed(() =>
  mqttStore.chargePointConnectedVehicleBidiChargeMinDischargeSoC(
    props.chargePointId,
  ),
);

const current = computed(() =>
  mqttStore.chargePointConnectedVehicleBidiChargeCurrent(props.chargePointId),
);

const planEtActive = computed(() =>
  mqttStore.chargePointConnectedVehicleBidiChargeEtActive(
    props.chargePointId,
  ),
);
</script>
