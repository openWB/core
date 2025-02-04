<template>
  <q-card class="rounded-borders-md">
    <q-card-section>
      <div class="row items-center q-mb-sm">
        <q-input v-model="planName.value" label="Plan Name" class="col" />
      </div>
      <div class="row items-center">
        <div class="text-subtitle2 q-mr-sm">Aktiv</div>
        <ToggleStandard v-model="planActive" :size="'sm'" color="positive" />
      </div>
      <div class="row items-center q-mb-md">
        <q-input
          v-model="planTime.value"
          type="time"
          label="Ziel-Uhrzeit"
          class="col"
        />
      </div>
      <SliderStandard
        class="q-mb-md"
        title="Stromstärke"
        :min="6"
        :max="32"
        unit="A"
        v-model="planCurrent.value"
      />
      <q-btn-group>
        <q-btn
          size="sm"
          :color="planLimitSelected.value === 'soc' ? 'primary' : 'grey'"
          @click="planLimitSelected.value = 'soc'"
          label="SoC"
        />
        <q-btn
          size="sm"
          :color="planLimitSelected.value === 'amount' ? 'primary' : 'grey'"
          @click="planLimitSelected.value = 'amount'"
          label="Amount"
        />
      </q-btn-group>
      <div v-if="planLimitSelected.value === 'soc'" class="q-mt-md">
        <SliderStandard
          title="EV-SoC"
          :min="5"
          :max="100"
          :step="5"
          unit="%"
          v-model="planSocScheduled.value"
          class="q-mt-sm"
        />
        <SliderStandard
          title="Fahrzeug-SoC mit Überschuss"
          :min="5"
          :max="100"
          :step="5"
          unit="%"
          v-model="planSocLimit.value"
        />
      </div>
      <q-input
        v-if="planLimitSelected.value === 'amount'"
        v-model="planLimitAmount.value"
        label="Energiemenge (kWh)"
        class="col"
      />
      <div class="q-mb-md">
        <div class="text-subtitle2 q-mb-sm q-mt-sm">Wiederholungen</div>
        <q-btn-group spread>
          <q-btn
            size="sm"
            :color="planFrequency.value === 'once' ? 'primary' : 'grey'"
            @click="planFrequency.value = 'once'"
            label="Einmalig"
          />
          <q-btn
            size="sm"
            :color="planFrequency.value === 'daily' ? 'primary' : 'grey'"
            @click="planFrequency.value = 'daily'"
            label="Täglich"
          />
          <q-btn
            size="sm"
            :color="planFrequency.value === 'weekly' ? 'primary' : 'grey'"
            @click="planFrequency.value = 'weekly'"
            label="Wöchentlich"
          />
        </q-btn-group>

        <div v-if="planFrequency.value === 'once'" class="q-mt-sm">
          <q-input
            v-model="planOnceDate.value"
            type="date"
            label="Datum"
            :min="new Date().toISOString().split('T')[0]"
          />
        </div>
        <!-- Weekly buttons -->
        <div
          v-if="planFrequency.value === 'weekly'"
          class="q-mt-sm row items-center q-gutter-sm justify-center no-wrap"
        >
          <div v-for="(day, index) in weekDays" :key="day">
            <q-btn
              round
              :size="$q.platform.is.mobile ? '0.8rem' : '0.7rem'"
              :flat="!selectedWeekDays[index]"
              :outline="selectedWeekDays[index]"
              color="primary"
              :label="day"
              :class="{ deselected: !selectedWeekDays[index] }"
              @click="selectDay(index)"
            />
          </div>
        </div>
        <div class="q-mt-lg row justify-end">
          <q-btn
            size="sm"
            icon="delete"
            :color="'primary'"
            label="Löschen"
            @click="deletePlan(props.chargePointId, props.plan.id)"
          />
        </div>
      </div>
    </q-card-section>
  </q-card>
</template>

<script setup lang="ts">
import { useMqttStore } from 'src/stores/mqtt-store';
import { useQuasar } from 'quasar';
import SliderStandard from './SliderStandard.vue';
import ToggleStandard from './ToggleStandard.vue';
import { computed } from 'vue';
import { type ScheduledChargingPlan } from '../stores/mqtt-store-model';

const props = defineProps<{
  chargePointId: number;
  plan: ScheduledChargingPlan;
}>();

const mqttStore = useMqttStore();
const $q = useQuasar();

const weekDays = ['Mo', 'Di', 'Mi', 'Do', 'Fr', 'Sa', 'So'];

const selectDay = (index: number) => {
  const newArray = [...selectedWeekDays.value];
  newArray[index] = !newArray[index];
  selectedWeekDays.value = newArray;
};

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

const planCurrent = computed(() =>
  mqttStore.vehicleScheduledChargingPlanCurrent(
    props.chargePointId,
    props.plan.id,
  ),
);

const planLimitSelected = computed(() =>
  mqttStore.vehicleScheduledChargingPlanLimitSelected(
    props.chargePointId,
    props.plan.id,
  ),
);

const planLimitAmount = computed(() =>
  mqttStore.vehicleScheduledChargingPlanEnergyAmount(
    props.chargePointId,
    props.plan.id,
  ),
);

const planName = computed(() =>
  mqttStore.vehicleScheduledChargingPlanName(
    props.chargePointId,
    props.plan.id,
  ),
);

const planTime = computed(() =>
  mqttStore.vehicleScheduledChargingPlanTime(
    props.chargePointId,
    props.plan.id,
  ),
);

const planFrequency = computed(() =>
  mqttStore.vehicleScheduledChargingPlanFrequencySelected(
    props.chargePointId,
    props.plan.id,
  ),
);

const planOnceDate = computed(() =>
  mqttStore.vehicleScheduledChargingPlanOnceDate(
    props.chargePointId,
    props.plan.id,
  ),
);

const selectedWeekDays = computed<boolean[]>({
  get() {
    return (
      mqttStore.vehicleScheduledChargingPlanWeeklyDays(
        props.chargePointId,
        props.plan.id,
      ).value ?? Array(7).fill(false)
    );
  },
  set(newValue: boolean[]) {
    mqttStore.vehicleScheduledChargingPlanWeeklyDays(
      props.chargePointId,
      props.plan.id,
    ).value = newValue;
  },
});

const planSocLimit = computed(() =>
  mqttStore.vehicleScheduledChargingPlanSocLimit(
    props.chargePointId,
    props.plan.id,
  ),
);

const planSocScheduled = computed(() =>
  mqttStore.vehicleScheduledChargingPlanSocScheduled(
    props.chargePointId,
    props.plan.id,
  ),
);

const deletePlan = (chargePointId: number, planId: string) =>
  mqttStore.vehicleDeleteScheduledChargingPlan(props.chargePointId, planId);
</script>

<style scoped>
.q-btn-group .q-btn {
  min-width: 100px !important;
  font-size: 10px !important;
}
</style>
