<template>
  <q-btn
    no-caps
    align="center"
    class="cursor-pointer"
    :color="planActive.value ? 'positive' : 'negative'"
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
