<template>
  <div
    class="row items-center q-ma-none q-pa-none no-wrap items-center justify-between"
  >
    <div class="text-subtitle2">Zeitladen</div>
    <div>
      <ChargePointTimeCharging :charge-point-id="props.chargePointId" dense />
    </div>
  </div>
  <div v-if="timeChargingEnabled" class="row justify-between items-center">
    <div class="text-subtitle2">Termine Zeitladen:</div>
  </div>
  <div
    v-if="plans.length === 0 && timeChargingEnabled"
    class="row q-mt-sm q-pa-sm bg-primary text-white no-wrap message-text"
    color="primary"
    style="border-radius: 10px"
  >
    <q-icon name="info" size="sm" class="q-mr-xs" />
    Keine Zeitpläne vorhanden.
  </div>
  <div v-else-if="timeChargingEnabled">
    <div v-for="(plan, index) in plans" :key="index" class="row q-mt-sm">
      <ChargePointTimeChargingPlanButton
        class="full-width"
        :charge-point-id="props.chargePointId"
        :plan="plan"
      />
    </div>
  </div>
</template>

<script setup lang="ts">
import { useMqttStore } from 'src/stores/mqtt-store';
import { computed } from 'vue';
import ChargePointTimeCharging from './ChargePointTimeCharging.vue';
import ChargePointTimeChargingPlanButton from './ChargePointTimeChargingPlanButton.vue';

const props = defineProps<{
  chargePointId: number;
}>();

const mqttStore = useMqttStore();

const plans = computed(() =>
  mqttStore.vehicleTimeChargingPlans(props.chargePointId),
);

const timeChargingEnabled = mqttStore.chargePointConnectedVehicleTimeCharging(
  props.chargePointId,
);
</script>
