<template>
  <q-btn
    flat
    no-caps
    align="center"
    class="scheduled-plan-button cursor-pointer"
    :class="planActive.value ? 'is-active' : 'is-inactive'"
    @click="$emit('editPlan', plan)"
  >
    <ChargePointScheduledPlanSummary
      :charge-point-id="props.chargePointId"
      :plan="props.plan"
    />
  </q-btn>
</template>

<script setup lang="ts">
import { computed } from 'vue';
import { useMqttStore } from 'src/stores/mqtt-store';
import ChargePointScheduledPlanSummary from './ChargePointScheduledPlanSummary.vue';
import { type ScheduledChargingPlan } from '../stores/mqtt-store-model';

const props = defineProps<{
  chargePointId: number;
  plan: ScheduledChargingPlan;
}>();

const mqttStore = useMqttStore();

const planActive = computed(() =>
  mqttStore.vehicleScheduledChargingPlanActive(
    props.chargePointId,
    props.plan.id,
  ),
);
</script>

<style scoped lang="scss">
.scheduled-plan-button.is-active {
  --plan-state: var(--q-positive);
}
.scheduled-plan-button.is-inactive {
  --plan-state: var(--q-negative);
}
.scheduled-plan-button {
  background-color: color-mix(in srgb, var(--plan-state) 30%, transparent);
  border: 1px solid color-mix(in srgb, var(--q-text) 35%, transparent);
  color: color-mix(in srgb, var(--q-text) 90%, transparent);
}
</style>
