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
      <div class="plan-details">
        <div>
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
            {{ formattedDateRange }}
          </div>
          <div v-if="plan.frequency.selected === 'weekly'">
            {{ selectedWeekDays }}
          </div>
          <div v-if="plan.frequency.selected === 'daily'">täglich</div>
        </div>
        <div>
          <q-icon name="schedule" size="sm" />
          <div>{{ plan.time[0] }}-{{ plan.time[1] }}</div>
        </div>
        <div v-if="plan.limit.selected !== 'none'">
          <q-icon
            :name="plan.limit.selected === 'soc' ? 'battery_full' : 'bolt'"
            size="sm"
          />
          <div v-if="plan.limit.selected === 'soc'">{{ plan.limit.soc }}%</div>
          <div v-if="plan.limit.selected === 'amount'">
            {{ plan.limit.amount ? plan.limit.amount / 1000 : '' }}kWh
          </div>
        </div>
      </div>
    </div>
  </q-btn>
</template>

<script setup lang="ts">
import { computed } from 'vue';
import { useMqttStore } from 'src/stores/mqtt-store';
import { type TimeChargingPlan } from '../stores/mqtt-store-model';

const props = defineProps<{
  chargePointId: number;
  plan: TimeChargingPlan;
}>();

const mqttStore = useMqttStore();

const weekdays = ['Mo', 'Di', 'Mi', 'Do', 'Fr', 'Sa', 'So'];

const planActive = computed(() =>
  mqttStore.vehicleTimeChargingPlanActive(props.chargePointId, props.plan.id),
);

const selectedWeekDays = computed(() => {
  let planDays: string[] = [];
  let rangeStart: number | null = null;

  props.plan.frequency.weekly.forEach((dayValue, index) => {
    if (dayValue) {
      if (rangeStart === null) {
        rangeStart = index;
      }
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
    if (rangeStart === props.plan.frequency.weekly.length - 1) {
      planDays.push(weekdays[rangeStart]);
    } else {
      planDays.push(
        `${weekdays[rangeStart]}-${weekdays[props.plan.frequency.weekly.length - 1]}`,
      );
    }
  }

  return planDays.join(', ');
});

const formattedDateRange = computed(() => {
  if (props.plan.frequency.once === undefined) return '-';
  const startDate = new Date(props.plan.frequency.once[0]);
  const endDate = new Date(props.plan.frequency.once[1]);
  const sameYear = startDate.getFullYear() === endDate.getFullYear();
  const sameMonth = startDate.getMonth() === endDate.getMonth() && sameYear;
  const sameDay = startDate.getDay() === endDate.getDay() && sameMonth;
  return `${
    sameDay
      ? ''
      : startDate.toLocaleDateString(undefined, {
          day: 'numeric',
          month: !sameMonth ? 'numeric' : undefined,
          year: !sameYear ? 'numeric' : undefined,
        }) + (sameMonth ? '.-' : '-')
  }${endDate.toLocaleDateString(undefined, {
    day: 'numeric',
    month: 'numeric',
    year: 'numeric',
  })}`;
});
</script>

<style scoped>
.full-width {
  width: 100%;
}
.plan-name {
  font-weight: bold;
}
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
body.mobile .height {
  height: 2.5em;
}
</style>
