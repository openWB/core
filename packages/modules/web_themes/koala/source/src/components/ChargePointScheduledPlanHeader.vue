<template>
  <div
    class="row items-center justify-between text-subtitle2 full-width no-wrap height"
  >
    <div class="row" @click="planActive.value = !planActive.value">
      <q-icon
        :name="
          plan.frequency.selected === 'once'
            ? 'today'
            : plan.frequency.selected === 'daily'
              ? 'date_range'
              : 'calendar_month'
        "
        size="sm"
        class="q-mr-xs white-icon"
        :title="
          plan.frequency.selected === 'once'
            ? 'Einmalig'
            : plan.frequency.selected === 'daily'
              ? 'Täglich'
              : 'Wöchentlich'
        "
      />
      <div
        v-if="plan.frequency.selected === 'once'"
        class="q-mr-xs white-text"
      >
        {{ formattedDate }}
      </div>
      <div
        v-if="plan.frequency.selected === 'weekly'"
        class="q-mr-xs white-text"
      >
        {{ selectedWeekDays }}
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
      <q-icon
        v-if="planEtActive.value"
        name="bar_chart"
        size="sm"
        class="q-mr-xs white-icon"
      />
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

const weekdays = ['Mo', 'Di', 'Mi', 'Do', 'Fr', 'Sa', 'So'];

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

const selectedWeekDays = computed(() => {
  return props.plan.frequency.weekly
    ? weekdays.filter((day, index) => props.plan.frequency.weekly[index]).join(', ')
    : '-';
});

const formattedDate = computed(() => {
  if (props.plan.frequency.once === undefined)
    return '-';
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
