<template>
  <div class="row justify-between items-center">
    <div class="text-subtitle2 q-mr-sm q-mt-md">Termine Zielladen:</div>
  </div>
  <div
    v-if="plans.length === 0"
    class="row q-mt-sm q-pa-sm bg-primary text-white no-wrap message-text"
    color="primary"
    style="border-radius: 10px"
  >
    <q-icon name="info" size="sm" class="q-mr-xs" />
    Keine Ladeziele festgelegt.
  </div>
  <div v-else>
    <div v-for="(plan, index) in plans" :key="index" class="row q-mt-sm">
      <ChargePointScheduledPlanButton
        class="full-width"
        :charge-point-id="props.chargePointId"
        :plan="plan"
      />
    </div>
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
