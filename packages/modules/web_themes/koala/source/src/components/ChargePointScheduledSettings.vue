<template>
  <div class="row justify-between items-center q-mt-md">
    <div class="text-subtitle2">Termine Zielladen:</div>
    <q-btn
      round
      size="sm"
      color="primary"
      icon="add"
      @click="addScheduledChargingPlan"
    />
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
        @edit-plan="openPlanDialog(plan)"
      />
    </div>
    <q-dialog
      v-model="currentPlanDetailsVisible"
      :maximized="isSmallScreen"
      :backdrop-filter="isSmallScreen ? '' : 'blur(4px)'"
    >
      <ChargePointScheduledPlanDetails
        v-if="selectedPlan"
        :charge-point-id="props.chargePointId"
        :plan="selectedPlan"
        @close="currentPlanDetailsVisible = false"
      />
    </q-dialog>
  </div>
</template>

<script setup lang="ts">
import { useMqttStore } from 'src/stores/mqtt-store';
import ChargePointScheduledPlanButton from './ChargePointScheduledPlanButton.vue';
import ChargePointScheduledPlanDetails from './ChargePointScheduledPlanDetails.vue';
import { computed, ref } from 'vue';
import { Screen } from 'quasar';

const props = defineProps<{
  chargePointId: number;
}>();

const isSmallScreen = computed(() => Screen.lt.sm);

const currentPlanDetailsVisible = ref<boolean>(false);
const selectedPlan = ref(null);

const mqttStore = useMqttStore();

const plans = computed(() =>
  mqttStore.vehicleScheduledChargingPlans(props.chargePointId),
);

const addScheduledChargingPlan = () => {
  mqttStore.addScheduledChargingPlanForChargePoint(props.chargePointId);
};

const openPlanDialog = (plan) => {
  selectedPlan.value = plan;
  currentPlanDetailsVisible.value = true;
};
</script>
