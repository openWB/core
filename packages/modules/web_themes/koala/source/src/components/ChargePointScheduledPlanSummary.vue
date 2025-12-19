<template>
  <div class="column">
    <div v-if="use === 'button'" class="plan-name">{{ plan.name }}</div>
    <div v-if="use === 'info'" class="plan-name">
      Nächster geplanter Termin:
    </div>
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
          {{ planOnceDate }}
        </div>
        <div v-if="plan.frequency.selected === 'weekly' && use === 'button'">
          {{ selectedWeekDaysLabels }}
        </div>
        <div v-if="plan.frequency.selected === 'weekly' && use === 'info'">
          {{ firstSelectedWeekday }}
        </div>
        <div v-if="plan.frequency.selected === 'daily' && use === 'button'">
          täglich
        </div>
        <div v-if="plan.frequency.selected === 'daily' && use === 'info'">
          {{ today }}
        </div>
      </div>
      <div>
        <q-icon name="schedule" size="sm" />
        <div>{{ plan.time }}</div>
      </div>
      <div>
        <q-icon
          :name="plan.limit.selected === 'soc' ? 'battery_full' : 'bolt'"
          size="sm"
        />
        <div v-if="plan.limit.selected === 'soc'">
          {{ plan.limit.soc_scheduled }}%
          <q-icon
            :name="plan.bidi_charging_enabled ? 'sync_alt' : 'arrow_right_alt'"
            size="sm"
          />
          {{ plan.limit.soc_limit }}%
        </div>
        <div v-if="plan.limit.selected === 'amount'">
          {{ plan.limit.amount ? plan.limit.amount / 1000 : '' }}kWh
        </div>
      </div>
      <div>
        <q-icon v-if="planEtActive.value" name="bar_chart" size="sm" />
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
  use: 'button' | 'info';
}>();

const mqttStore = useMqttStore();

const weekdays = ['Mo', 'Di', 'Mi', 'Do', 'Fr', 'Sa', 'So'];
const formatDateDayMonthYear = (dateString: string): string => {
  if (!dateString) return '';
  const [year, month, day] = dateString.split('-');
  return `${day}.${month}.${year}`;
};
const today = formatDateDayMonthYear(new Date().toISOString().split('T')[0]);

const selectedWeekDays = computed<boolean[]>(() => {
  return (
    mqttStore.vehicleScheduledChargingPlanWeeklyDays(
      props.chargePointId,
      props.plan.id,
    ).value ?? Array(7).fill(false)
  );
});
// String label for button mode ("Mo-Fr, So")
const selectedWeekDaysLabels = computed(() => {
  const selected = selectedWeekDays.value;
  const planDays: string[] = [];
  let rangeStart: number | null = null;
  selected.forEach((isSelected, index) => {
    if (isSelected) {
      if (rangeStart === null) {
        rangeStart = index;
      }
    } else if (rangeStart !== null) {
      if (rangeStart === index - 1) {
        planDays.push(weekdays[rangeStart]);
      } else {
        planDays.push(`${weekdays[rangeStart]}-${weekdays[index - 1]}`);
      }
      rangeStart = null;
    }
  });
  if (rangeStart !== null) {
    const lastIndex = selected.length - 1;
    if (rangeStart === lastIndex) {
      planDays.push(weekdays[rangeStart]);
    } else {
      planDays.push(`${weekdays[rangeStart]}-${weekdays[lastIndex]}`);
    }
  }
  return planDays.join(', ');
});

const firstSelectedWeekday = computed(() => {
  const today = new Date();
  // 0=Sonntag, ..., 6=Samstag >> 0=Montag, ..., 6=Sonntag
  const todayIndex = (today.getDay() + 6) % 7;
  const userSelection = selectedWeekDays.value
    .map((isSelected, index) => (isSelected ? index : -1))
    .filter((index) => index !== -1);
  if (userSelection.length === 0) return '';
  // For all selected days, calculate the distance to today
  const daysUntilSelected = userSelection.map((idx) => {
    let daysUntil = idx - todayIndex;
    if (daysUntil < 0) daysUntil += 7;
    return daysUntil;
  });
  // Take the smallest distance (this is the next day)
  const nearestDay = Math.min(...daysUntilSelected);
  const dateNextDay = new Date(today);
  dateNextDay.setDate(today.getDate() + nearestDay);
  return formatDateDayMonthYear(dateNextDay.toISOString().split('T')[0]);
});

const planOnceDate = computed(() => {
  if (props.plan.frequency.once === undefined) return '-';
  const date = new Date(props.plan.frequency.once);
  return formatDateDayMonthYear(date.toISOString().split('T')[0]);
});

const planEtActive = computed(() =>
  mqttStore.vehicleScheduledChargingPlanEtActive(
    props.chargePointId,
    props.plan.id,
  ),
);
</script>

<style scoped lang="scss">
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
  margin-right: #{map-get($space-sm, x)};
}
</style>
