<template>
  <div class="row justify-between items-center">
    <div class="text-subtitle2 q-mr-sm q-mt-md">Termine:</div>
  </div>
  <div
    v-for="(plan, index) in plans.value"
    :key="index"
    class="row q-mt-sm"
  >
    <ChargePointScheduledPlanButton
      class="full-width"
      :charge-point-id="props.chargePointId"
      :plan="plan"
    />
  </div>
</template>

<script setup lang="ts">
import { useMqttStore } from 'src/stores/mqtt-store';
import ChargePointScheduledPlanButton from './ChargePointScheduledPlanButton.vue';
import { computed } from 'vue';

const props = defineProps<{
  chargePointId: number;
}>();

const mqttStore = useMqttStore();

const plans = computed(() =>
  mqttStore.vehicleScheduledChargingPlans(props.chargePointId),
);
</script>

<style scoped>
.full-width {
  width: 100%;
}
</style>
