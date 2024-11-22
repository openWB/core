<template>
  <div
    class="row items-center justify-between text-subtitle2 full-width no-wrap"
  >
    <div class="row" @click="togglePlanActive = !togglePlanActive">
      <q-icon
        :name="
          plan.frequency.selected === 'daily'
            ? 'calendar_today'
            : plan.frequency.selected === 'weekly'
              ? 'calendar_month'
              : 'event'
        "
        size="sm"
        class="q-mr-xs"
      />
      <div class="q-mr-xs">
        {{
          plan.frequency.selected === 'daily'
            ? 'täglich'
            : plan.frequency.selected === 'weekly'
              ? plan.frequency.selected_days
                ? plan.frequency.selected_days.join(', ')
                : ''
              : 'einmalig'
        }}
      </div>
      <q-icon name="schedule" size="sm" class="q-mr-xs" />
      <div class="q-mr-xs">{{ plan.time }}</div>
      <q-icon
        :name="plan.limit.selected === 'soc' ? 'battery_full' : 'bolt'"
        size="sm"
        class="q-mr-xs"
      />
      <div v-if="plan.limit.selected === 'soc'" class="q-mr-xs">
        {{ plan.limit.soc_scheduled }}%
      </div>
      <div v-if="plan.limit.selected === 'amount'" class="q-mr-xs">
        {{ plan.limit.amount ? plan.limit.amount / 1000 : '' }}kWh
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue';
import { useMqttStore } from 'src/stores/mqtt-store';
import { type ScheduledChargingPlan } from '../stores/mqtt-store-model';

const props = defineProps<{
  chargePointId: number;
  plan: ScheduledChargingPlan;
}>();

const mqttStore = useMqttStore();

const togglePlanActive = computed({
  get() {
    return mqttStore.vehicleToggleScheduledChargingPlanActive(
      props.chargePointId,
      props.plan.id,
    ).value;
  },
  set() {
    const currentValue = mqttStore.vehicleToggleScheduledChargingPlanActive(
      props.chargePointId,
      props.plan.id,
    ).value;
    mqttStore.vehicleToggleScheduledChargingPlanActive(
      props.chargePointId,
      props.plan.id,
    ).value = !currentValue;
  },
});
</script>
