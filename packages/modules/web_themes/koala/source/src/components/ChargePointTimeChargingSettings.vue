<template>
  <div
    class="row items-center q-ma-none q-pa-none no-wrap items-center justify-between"
  >
    <div class="text-subtitle2">Zeitladen</div>

    <div>
      <ChargePointTimeCharging :charge-point-id="props.chargePointId" dense />
    </div>
  </div>
  <div
    v-if="timeChargingEnabled"
    class="row justify-between items-center q-mt-md"
  >
    <div class="text-subtitle2">Termine Zeitladen:</div>
    <div class="row q-mb-md justify-end">
      <q-btn
        round
        outline
        size="sm"
        color="primary"
        icon="add"
        @click="addScheduledChargingPlan"
      />
    </div>
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
        @edit="openPlanDialog(plan)"
      />
    </div>

    <q-dialog
      v-model="currentPlanDetailsVisible"
      :maximized="isSmallScreen"
      :backdrop-filter="isSmallScreen ? '' : 'blur(4px)'"
    >
      <ChargePointTimeChargingPlanDetails
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
import { computed, ref } from 'vue';
import ChargePointTimeCharging from './ChargePointTimeCharging.vue';
import ChargePointTimeChargingPlanButton from './ChargePointTimeChargingPlanButton.vue';
import ChargePointTimeChargingPlanDetails from './ChargePointTimeChargingPlanDetails.vue';
import { Screen } from 'quasar';

const props = defineProps<{
  chargePointId: number;
}>();

const isSmallScreen = computed(() => Screen.lt.sm);

const currentPlanDetailsVisible = ref<boolean>(false);
const selectedPlan = ref(null);

const mqttStore = useMqttStore();

const plans = computed(() =>
  mqttStore.vehicleTimeChargingPlans(props.chargePointId),
);

const timeChargingEnabled = mqttStore.chargePointConnectedVehicleTimeCharging(
  props.chargePointId,
);

const addScheduledChargingPlan = () => {
  mqttStore.addTimeChargingPlanForChargePoint(props.chargePointId);
};

const openPlanDialog = (plan) => {
  selectedPlan.value = plan;
  currentPlanDetailsVisible.value = true;
};
</script>
