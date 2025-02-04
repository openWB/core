<template>
  <div class="row justify-between items-center">
    <div class="text-subtitle2 q-mr-sm q-mt-md">Termine:</div>
    <q-btn
      icon="add"
      color="primary"
      round
      size="sm"
      class="q-mt-md"
      @click="mqttStore.vehicleAddScheduledChargingPlan(props.chargePointId)"
    />
  </div>
  <q-expansion-item
    v-for="(plan, index) in plans.value"
    :key="index"
    expand-icon-toggle
    :default-opened="false"
    class="q-mt-md bg-primary rounded-borders-md"
    :class="plan.active ? 'active-border' : 'inactive-border'"
    :header-class="'cursor-pointer'"
    dense
  >
    <template v-slot:header>
      <ChargePointScheduledPlanHeader
        :charge-point-id="props.chargePointId"
        :plan="plan"
      />
    </template>
    <ChargePointScheduledPlanDetails
      :charge-point-id="props.chargePointId"
      :plan="plan"
    />
  </q-expansion-item>
</template>

<script setup lang="ts">
import { useMqttStore } from 'src/stores/mqtt-store';
import ChargePointScheduledPlanHeader from './ChargePointScheduledPlanHeader.vue';
import ChargePointScheduledPlanDetails from './ChargePointScheduledPlanDetails.vue';
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
.rounded-borders-md {
  border-radius: 8px;
}
.active-border {
  box-shadow: 0 0 0 4px var(--q-positive);
}
.inactive-border {
  box-shadow: 0 0 0 4px var(--q-negative);
}
:deep(.q-expansion-item__container) .q-item {
  padding: 6px 6px;
}
</style>
