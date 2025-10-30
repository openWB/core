<template>
  <q-btn
    no-caps
    align="center"
    class="cursor-pointer"
    :color="planActive.value ? 'positive' : 'negative'"
    @click="$emit('edit', plan)"
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
            {{ formattedDate }}
          </div>
          <div v-if="plan.frequency.selected === 'weekly'">
            {{ selectedWeekDays }}
          </div>
          <div v-if="plan.frequency.selected === 'daily'">täglich</div>
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
              :name="
                plan.bidi_charging_enabled ? 'sync_alt' : 'arrow_right_alt'
              "
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
