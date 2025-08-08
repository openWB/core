<template>
  <q-btn
    no-caps
    align="center"
    class="cursor-pointer"
    :color="planActive.value ? 'positive' : 'negative'"
    @click="planActive.value = !planActive.value"
  >
    <div class="column">
      <div class="plan-name">{{ plan.name }}</div>
      <PlanDetailsDisplay
        :frequency="plan.frequency.selected"
        :time="plan.time"
        :limitType="plan.limit.selected"
        :socScheduled="plan.limit.soc_scheduled"
        :amount="plan.limit.amount ? plan.limit.amount / 1000 : undefined"
        :date="plan.frequency.once"
        :weeklyDays="plan.frequency.weekly"
        :etActive="planEtActive.value"
      />
    </div>
  </q-btn>
</template>

<script setup lang="ts">
import { computed } from 'vue';
import { useMqttStore } from 'src/stores/mqtt-store';
import PlanDetailsDisplay from './PlanDetailsDisplay.vue';
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

const planEtActive = computed(() =>
  mqttStore.vehicleScheduledChargingPlanEtActive(
    props.chargePointId,
    props.plan.id,
  ),
);
</script>
