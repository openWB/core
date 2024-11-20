<template>
  <div
    class="row items-center justify-between text-subtitle2 full-width no-wrap"
    @click.stop
  >
    <div class="row" @click="togglePlanActive(plan.id)">
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
    <q-btn
      icon="delete"
      flat
      round
      size="md"
      color="white"
      @click="
        mqttStore.vehicleDeleteScheduledChargingPlan(
          props.chargePointId,
          plan.id,
        )
      "
    />
  </div>
</template>

<script setup lang="ts">
import { useMqttStore } from 'src/stores/mqtt-store';
import { type ScheduledChargingPlan } from '../stores/mqtt-store-model';

const props = defineProps<{
  chargePointId: number;
  plan: ScheduledChargingPlan;
}>();

const mqttStore = useMqttStore();

const togglePlanActive = (planId: string) =>
  mqttStore.vehicleToggleScheduledChargingPlanActive(
    props.chargePointId,
    planId,
  );
</script>
