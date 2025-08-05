<template>
  <SliderStandard
    title="Minimaler Entlade-SoC"
    :min="5"
    :max="100"
    :step="5"
    unit="%"
    v-model="minEntladeSoc.value"
    class="q-mt-md"
  />
  <SliderStandard
    title="Ladestrom"
    :min="6"
    :max="32"
    :step="1"
    unit="A"
    v-model="current.value"
    class="q-mt-md"
  />
  <div class="text-subtitle2 q-mr-sm q-mt-md">Bidi-Plan:</div>

  <div class="column q-mt-sm">
    <div class="plan-details">
      <div>
        <q-icon
          :name="
            plan?.frequency.selected === 'once'
              ? 'today'
              : plan?.frequency.selected === 'daily'
                ? 'date_range'
                : 'calendar_month'
          "
          size="sm"
          :title="
            plan?.frequency.selected === 'once'
              ? 'Einmalig'
              : plan?.frequency.selected === 'daily'
                ? 'Täglich'
                : 'Wöchentlich'
          "
        />
        <div v-if="plan?.frequency.selected === 'once'">
          {{ formattedDate }}
        </div>
        <div v-if="plan?.frequency.selected === 'weekly'">
          {{ selectedWeekDays }}
        </div>
        <div v-if="plan?.frequency.selected === 'daily'">täglich</div>
      </div>
      <div>
        <q-icon name="schedule" size="sm" />
        <div>{{ plan?.time }}</div>
      </div>
      <div>
        <q-icon name="battery_full" size="sm" />
        <div>{{ plan?.limit.soc_scheduled }}%</div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { useMqttStore } from 'src/stores/mqtt-store';
import { computed } from 'vue';
import SliderStandard from './SliderStandard.vue';

const props = defineProps<{
  chargePointId: number;
}>();

const mqttStore = useMqttStore();

const weekdays = ['Mo', 'Di', 'Mi', 'Do', 'Fr', 'Sa', 'So'];

const plan = computed(() =>
  mqttStore.chargePointConnectedVehicleBidiChargePlan(props.chargePointId),
);

const formattedDate = computed(() => {
  if (plan.value?.frequency.once === undefined) return '-';
  const date = new Date(plan.value.frequency.once);
  return date.toLocaleDateString(undefined, {
    day: '2-digit',
    month: '2-digit',
    year: 'numeric',
  });
});

const selectedWeekDays = computed(() => {
  let planDays: string[] = [];
  let rangeStart: number | null = null;

  plan.value?.frequency.weekly.forEach((dayValue, index) => {
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
    if (
      plan.value?.frequency?.weekly &&
      rangeStart === plan.value.frequency.weekly.length - 1
    ) {
      planDays.push(weekdays[rangeStart]);
    } else if (plan.value?.frequency?.weekly) {
      planDays.push(
        `${weekdays[rangeStart]}-${weekdays[plan.value.frequency.weekly.length - 1]}`,
      );
    }
  }

  return planDays.join(', ');
});

const minEntladeSoc = computed(() =>
  mqttStore.chargePointConnectedVehicleBidiChargeMinEntladeSoC(
    props.chargePointId,
  ),
);

const current = computed(() =>
  mqttStore.chargePointConnectedVehicleBidiChargeCurrent(props.chargePointId),
);
</script>

<style scoped>
.full-width {
  width: 100%;
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
