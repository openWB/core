<template>
  <div
    class="row items-center justify-between text-subtitle2 full-width no-wrap height"
  >
    <div class="row" @click="planActive = !planActive">
      <q-icon
        :name="
          plan.frequency.selected === 'daily'
            ? 'calendar_today'
            : plan.frequency.selected === 'weekly'
              ? 'calendar_month'
              : 'event'
        "
        size="sm"
        class="q-mr-xs white-icon"
      />
      <div class="q-mr-xs white-text">
        {{
          plan.frequency.selected === 'daily'
            ? 'täglich'
            : plan.frequency.selected === 'weekly'
              ? plan.frequency.selected_days
                ? plan.frequency.selected_days.join(', ')
                : ''
              : formattedDate
        }}
      </div>
      <q-icon name="schedule" size="sm" class="q-mr-xs white-icon" />
      <div class="q-mr-xs white-text">{{ plan.time }}</div>
      <q-icon
        :name="plan.limit.selected === 'soc' ? 'battery_full' : 'bolt'"
        size="sm"
        class="q-mr-xs white-icon"
      />
      <div v-if="plan.limit.selected === 'soc'" class="q-mr-xs white-text">
        {{ plan.limit.soc_scheduled }}%
      </div>
      <div v-if="plan.limit.selected === 'amount'" class="q-mr-xs white-text">
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

const planActive = computed({
  get() {
    return mqttStore.vehicleScheduledChargingPlanActive(
      props.chargePointId,
      props.plan.id,
    ).value;
  },
  set(newValue: boolean) {
    mqttStore.vehicleScheduledChargingPlanActive(
      props.chargePointId,
      props.plan.id,
    ).value = newValue;
  },
});

const formattedDate = computed(() => {
  if (!props.plan.frequency.once) return 'Datum wählen';
  const date = new Date(props.plan.frequency.once);
  return date.toLocaleDateString('de-DE', {
    day: '2-digit',
    month: '2-digit',
    year: 'numeric',
  });
});
</script>

<style scoped>
body.mobile .height {
  height: 2.5em;
}
.white-text {
  color: var(--q-white);
}
.white-icon {
  color: var(--q-white);
}
</style>
