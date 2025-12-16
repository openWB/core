<template>
  <q-card class="rounded-borders-md">
    <q-card-section>
      <div class="row no-wrap">
        <div class="text-h6 ellipsis" :title="planName.value">
          {{ planName.value }}
        </div>
        <q-space />
        <q-btn icon="close" flat round dense v-close-popup />
      </div>
    </q-card-section>
    <q-separator />
    <q-card-section>
      <div class="row items-center q-mb-sm">
        <q-input v-model="planName.value" label="Plan Name" class="col" />
      </div>
      <div class="row items-center justify-between">
        <div class="text-subtitle2 q-mr-sm">Aktiv</div>
        <ToggleStandard
          v-model="planActive.value"
          :size="'sm'"
          color="positive"
        />
      </div>
      <div class="row items-center q-mb-md">
        <q-input
          v-model="planStartTime.value"
          type="time"
          label="Ladebeginn"
          class="col q-mr-md"
        />
        <q-input
          v-model="planEndTime.value"
          type="time"
          label="Ladeende"
          class="col"
        />
      </div>
      <div class="q-mb-sm">
        <div class="text-subtitle2 q-mt-md">Wiederholungen</div>
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
            v-model="planOnceDateStart.value"
            type="date"
            label="Gültig ab"
            :min="new Date().toISOString().split('T')[0]"
          />
          <q-input
            v-model="planOnceDateEnd.value"
            type="date"
            label="Gültig bis"
            :min="planOnceDateStart.value"
          />
        </div>
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
      </div>
      <SliderStandard
        class="q-mb-sm"
        :title="planDcChargingEnabled ? 'Ladestrom (AC)' : 'Ladestrom'"
        :min="6"
        :max="32"
        unit="A"
        v-model="planCurrent.value"
      />
      <q-input
        v-if="planDcChargingEnabled"
        v-model="planDcPower.value"
        label="Ladeleistung (DC)"
        class="col q-mb-sm"
      >
        <template v-slot:append>
          <div class="text-body2">kW</div>
        </template>
      </q-input>
      <div class="text-subtitle2 q-mr-sm">Anzahl Phasen</div>
      <div class="row items-center justify-center q-ma-none q-pa-none no-wrap">
        <q-btn-group class="col">
          <q-btn
            v-for="option in phaseOptions"
            :key="option.value"
            :color="planNumPhases.value === option.value ? 'primary' : 'grey'"
            :label="option.label"
            size="sm"
            class="col"
            @click="planNumPhases.value = option.value"
          />
        </q-btn-group>
      </div>
      <div class="text-subtitle2 q-mt-sm">Begrenzung</div>
      <q-btn-group class="full-width">
        <q-btn
          size="sm"
          class="flex-grow"
          :color="planLimitSelected.value === 'none' ? 'primary' : 'grey'"
          @click="planLimitSelected.value = 'none'"
          label="Keine"
        />
        <q-btn
          size="sm"
          class="flex-grow"
          :color="planLimitSelected.value === 'soc' ? 'primary' : 'grey'"
          @click="planLimitSelected.value = 'soc'"
          label="EV-SoC"
        />
        <q-btn
          size="sm"
          class="flex-grow"
          :color="planLimitSelected.value === 'amount' ? 'primary' : 'grey'"
          @click="planLimitSelected.value = 'amount'"
          label="Energie"
        />
      </q-btn-group>
      <div v-if="planLimitSelected.value === 'soc'" class="q-mt-md">
        <SliderStandard
          title="SoC-Limit für das Fahrzeug"
          :min="5"
          :max="100"
          :step="5"
          unit="%"
          v-model="planSocLimit.value"
          class="q-mt-sm"
        />
      </div>
      <q-input
        v-if="planLimitSelected.value === 'amount'"
        v-model="planLimitAmount.value"
        label="Energie-Limit"
        class="col"
      >
        <template v-slot:append>
          <div class="text-body2">kWh</div>
        </template>
      </q-input>
      <div class="row q-mt-lg">
        <q-btn
          size="sm"
          class="col"
          color="negative"
          @click="removeTimeChargingPlan(plan.id)"
          >Plan löschen</q-btn
        >
      </div>
    </q-card-section>
  </q-card>
</template>

<script setup lang="ts">
import { useMqttStore } from 'src/stores/mqtt-store';
import SliderStandard from './SliderStandard.vue';
import ToggleStandard from './ToggleStandard.vue';
import { type TimeChargingPlan } from '../stores/mqtt-store-model';
import { computed } from 'vue';

const props = defineProps<{
  chargePointId: number;
  plan: TimeChargingPlan;
}>();

const mqttStore = useMqttStore();
const emit = defineEmits(['close']);

const weekDays = ['Mo', 'Di', 'Mi', 'Do', 'Fr', 'Sa', 'So'];

const phaseOptions = [
  { value: 1, label: '1' },
  { value: 3, label: 'Maximum' },
];

const selectDay = (index: number) => {
  const newArray = [...selectedWeekDays.value];
  newArray[index] = !newArray[index];
  selectedWeekDays.value = newArray;
};

// Hier die Computed Properties für die Felder (Backend-Anbindung folgt später)
const planName = computed(() =>
  mqttStore.vehicleTimeChargingPlanName(props.chargePointId, props.plan.id),
);
const planActive = computed(() =>
  mqttStore.vehicleTimeChargingPlanActive(props.chargePointId, props.plan.id),
);
const planCurrent = computed(() =>
  mqttStore.vehicleTimeChargingPlanCurrent(props.chargePointId, props.plan.id),
);
const planLimitSelected = computed(() =>
  mqttStore.vehicleTimeChargingPlanLimitSelected(
    props.chargePointId,
    props.plan.id,
  ),
);
const planLimitAmount = computed(() =>
  mqttStore.vehicleTimeChargingPlanEnergyAmount(
    props.chargePointId,
    props.plan.id,
  ),
);
const planSocLimit = computed(() =>
  mqttStore.vehicleTimeChargingPlanSocLimit(props.chargePointId, props.plan.id),
);
const planStartTime = computed(() =>
  mqttStore.vehicleTimeChargingPlanStartTime(
    props.chargePointId,
    props.plan.id,
  ),
);
const planEndTime = computed(() =>
  mqttStore.vehicleTimeChargingPlanEndTime(props.chargePointId, props.plan.id),
);
const planFrequency = computed(() =>
  mqttStore.vehicleTimeChargingPlanFrequencySelected(
    props.chargePointId,
    props.plan.id,
  ),
);
const planOnceDateStart = computed(() =>
  mqttStore.vehicleTimeChargingPlanOnceDateStart(
    props.chargePointId,
    props.plan.id,
  ),
);
const planOnceDateEnd = computed(() =>
  mqttStore.vehicleTimeChargingPlanOnceDateEnd(
    props.chargePointId,
    props.plan.id,
  ),
);
const selectedWeekDays = computed<boolean[]>({
  get() {
    return (
      mqttStore.vehicleTimeChargingPlanWeeklyDays(
        props.chargePointId,
        props.plan.id,
      ).value ?? Array(7).fill(false)
    );
  },
  set(newValue: boolean[]) {
    mqttStore.vehicleTimeChargingPlanWeeklyDays(
      props.chargePointId,
      props.plan.id,
    ).value = newValue;
  },
});

const planNumPhases = computed(() =>
  mqttStore.vehicleTimeChargingPlanPhases(props.chargePointId, props.plan.id),
);

const planDcChargingEnabled = computed(() => mqttStore.dcChargingEnabled);

const planDcPower = computed(() =>
  mqttStore.vehicleTimeChargingPlanDcPower(props.chargePointId, props.plan.id),
);

const removeTimeChargingPlan = (planId: number) => {
  mqttStore.removeTimeChargingPlanForChargePoint(props.chargePointId, planId);
  emit('close');
};
</script>

<style scoped>
.q-btn-group .q-btn {
  min-width: 100px !important;
  font-size: 10px !important;
}
.flex-grow {
  flex-grow: 1;
}
</style>
