<template>
  <q-btn
    no-caps
    align="between"
    class="cursor-pointer row"
    :color="planActive.value ? 'positive' : 'negative'"
    @click="planActive.value = !planActive.value"
  >
    <div class="row items-center no-wrap full-width">
      <div class="col text-left">{{ plan.name }}</div>
      <div class="col-auto row items-center">
        <q-icon
          :name="
            plan.frequency.selected === 'once'
              ? 'today'
              : plan.frequency.selected === 'daily'
                ? 'date_range'
                : 'calendar_month'
          "
          size="sm"
          :title="
            plan.frequency.selected === 'once'
              ? 'Einmalig'
              : plan.frequency.selected === 'daily'
                ? 'Täglich'
                : 'Wöchentlich'
          "
        />
        <div v-if="plan.frequency.selected === 'once'">
          {{ formattedDate }}
        </div>
        <div v-if="plan.frequency.selected === 'weekly'">
          {{ selectedWeekDays }}
        </div>
        <q-icon name="schedule" size="sm" />
        <div>{{ plan.time }}</div>
        <q-icon
          :name="plan.limit.selected === 'soc' ? 'battery_full' : 'bolt'"
          size="sm"
        />
        <div v-if="plan.limit.selected === 'soc'">
          {{ plan.limit.soc_scheduled }}%
        </div>
        <div v-if="plan.limit.selected === 'amount'">
          {{ plan.limit.amount ? plan.limit.amount / 1000 : '' }}kWh
        </div>
        <q-icon
          v-if="planEtActive.value"
          name="bar_chart"
          size="sm"
        />
      </div>
    </div>
  </q-btn>
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
    ? weekdays
        .filter((day, index) => props.plan.frequency.weekly[index])
        .join(', ')
    : '-';
});

const formattedDate = computed(() => {
  if (props.plan.frequency.once === undefined) return '-';
  const date = new Date(props.plan.frequency.once);
  return date.toLocaleDateString(undefined, {
    day: '2-digit',
    month: '2-digit',
    year: 'numeric',
  });
});
</script>

<style scoped>
.full-width {
  width: 100%;
}
body.mobile .height {
  height: 2.5em;
}
</style>
