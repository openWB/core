<template>
  <div class="plan-details">
    <div>
      <q-icon :name="iconName" size="sm" :title="iconTitle" />
      <div v-if="frequency === 'once'">{{ formattedDate }}</div>
      <div v-if="frequency === 'weekly'">{{ selectedWeekDays }}</div>
      <div v-if="frequency === 'daily'">täglich</div>
    </div>
    <div>
      <q-icon name="schedule" size="sm" />
      <div>{{ time }}</div>
    </div>
    <div>
      <q-icon :name="limitIcon" size="sm" />
      <div v-if="limitType === 'soc'">{{ socScheduled }}%</div>
      <div v-if="limitType === 'amount'">{{ amount }}kWh</div>
    </div>
    <q-icon v-if="props.etActive" name="bar_chart" size="sm" />
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue';

const iconName = computed(() =>
  props.frequency === 'once'
    ? 'today'
    : props.frequency === 'daily'
      ? 'date_range'
      : 'calendar_month',
);

const iconTitle = computed(() =>
  props.frequency === 'once'
    ? 'Einmalig'
    : props.frequency === 'daily'
      ? 'Täglich'
      : 'Wöchentlich',
);

const limitIcon = computed(() =>
  props.limitType === 'soc' ? 'battery_full' : 'bolt',
);

const weekdays = ['Mo', 'Di', 'Mi', 'Do', 'Fr', 'Sa', 'So'];

const props = defineProps<{
  frequency: string | undefined;
  time: string | undefined;
  limitType: string;
  socScheduled?: number;
  amount?: number;
  date?: string;
  weeklyDays?: boolean[];
  limitIcon?: string;
  etActive?: boolean;
}>();

const formattedDate = computed(() => {
  if (!props.date) return '-';
  const date = new Date(props.date);
  return date.toLocaleDateString(undefined, {
    day: '2-digit',
    month: '2-digit',
    year: 'numeric',
  });
});

const selectedWeekDays = computed(() => {
  if (!props.weeklyDays) return '';
  let planDays: string[] = [];
  let rangeStart: number | null = null;
  props.weeklyDays.forEach((dayValue, index) => {
    if (dayValue) {
      if (rangeStart === null) rangeStart = index;
    } else {
      if (rangeStart !== null) {
        if (rangeStart === index - 1) {
          planDays.push(weekdays[rangeStart]);
        } else {
          planDays.push(`${weekdays[rangeStart]}-${weekdays[index - 1]}`);
        }
        rangeStart = null;
      }
    }
  });
  // Handle the case where the last day(s) of the week are true
  if (rangeStart !== null) {
    if (rangeStart === props.weeklyDays.length - 1) {
      planDays.push(weekdays[rangeStart]);
    } else {
      planDays.push(
        `${weekdays[rangeStart]}-${weekdays[props.weeklyDays.length - 1]}`,
      );
    }
  }
  return planDays.join(', ');
});
</script>

<style scoped>
.plan-details {
  display: flex;
  justify-content: center;
}
.plan-details > div {
  display: flex;
  align-items: center;
}
.plan-details > div:not(:last-child) {
  margin-right: 0.5em;
}
</style>
