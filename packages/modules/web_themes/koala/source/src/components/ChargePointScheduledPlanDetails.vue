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
          v-model="planTime.value"
          type="time"
          label="Ziel-Uhrzeit"
          class="col"
        />
      </div>
      <div class="q-mb-sm">
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
        class="col q-mb-md"
      >
        <template v-slot:append>
          <div class="text-body2">kW</div>
        </template>
      </q-input>
      <div class="text-subtitle2 q-mr-sm">Anzahl Phasen Zielladen</div>
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
      <div class="text-subtitle2 q-mt-md q-mr-sm">
        Anzahl Phasen bei PV-Überschuss
      </div>
      <div class="row items-center justify-center q-ma-none q-pa-none no-wrap">
        <q-btn-group class="col">
          <q-btn
            v-for="option in phaseOptions"
            :key="option.value"
            :color="planNumPhasesPv.value === option.value ? 'primary' : 'grey'"
            :label="option.label"
            size="sm"
            class="col"
            @click="planNumPhasesPv.value = option.value"
          />
        </q-btn-group>
      </div>
      <div class="text-subtitle2 q-mt-sm q-mr-sm">Ziel</div>
      <q-btn-group class="full-width">
        <q-btn
          size="sm"
          class="flex-grow"
          :color="planLimitSelected.value === 'soc' ? 'primary' : 'grey'"
          @click="planLimitSelected.value = 'soc'"
          label="SoC"
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
        label="Ziel-Energie"
        class="col"
      >
        <template v-slot:append>
          <div class="text-body2">kWh</div>
        </template>
      </q-input>
      <div
        v-if="
          planLimitSelected.value === 'soc' &&
          chargePointConnectedVehicleBidiEnabled
        "
        class="row items-center justify-between"
      >
        <div class="text-subtitle2 q-mr-sm">
          Bidirektionales Überschussladen
        </div>
        <ToggleStandard
          v-model="planBidiEnabled.value"
          :size="'sm'"
          color="positive"
        />
      </div>
      <q-input
        v-if="
          planLimitSelected.value === 'soc' &&
          chargePointConnectedVehicleBidiEnabled &&
          planBidiEnabled.value
        "
        v-model="planBidiPower.value"
        label="Bidirektionales Ladeleistung (kW)"
        class="col"
      />
      <div class="row items-center justify-between">
        <div class="text-subtitle2 q-mr-sm">Strompreisbasiert laden</div>
        <ToggleStandard
          v-model="planEtActive.value"
          :size="'sm'"
          color="positive"
        />
      </div>
      <div class="row q-mt-md">
        <q-btn
          size="sm"
          class="col"
          color="negative"
          @click="removeScheduledChargingPlan(plan.id)"
          >Plan löschen</q-btn
        >
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

const emit = defineEmits(['close']);
const mqttStore = useMqttStore();
const $q = useQuasar();

const weekDays = ['Mo', 'Di', 'Mi', 'Do', 'Fr', 'Sa', 'So'];

const phaseOptions = [
  { value: 1, label: '1' },
  { value: 3, label: 'Maximum' },
  { value: 0, label: 'Automatik' },
];

const selectDay = (index: number) => {
  const newArray = [...selectedWeekDays.value];
  newArray[index] = !newArray[index];
  selectedWeekDays.value = newArray;
};

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

const planNumPhases = computed(() =>
  mqttStore.vehicleScheduledChargingPlanPhases(
    props.chargePointId,
    props.plan.id,
  ),
);

const planNumPhasesPv = computed(() =>
  mqttStore.vehicleScheduledChargingPlanPhasesPv(
    props.chargePointId,
    props.plan.id,
  ),
);

const planBidiEnabled = computed(() =>
  mqttStore.vehicleScheduledChargingPlanBidiEnabled(
    props.chargePointId,
    props.plan.id,
  ),
);

const planBidiPower = computed(() =>
  mqttStore.vehicleScheduledChargingPlanBidiPower(
    props.chargePointId,
    props.plan.id,
  ),
);

const chargePointConnectedVehicleBidiEnabled = computed(
  () =>
    mqttStore.chargePointConnectedVehicleBidiEnabled(props.chargePointId).value,
);

const planDcChargingEnabled = computed(() => mqttStore.dcChargingEnabled);

const planDcPower = computed(() =>
  mqttStore.vehicleScheduledChargingPlanDcPower(
    props.chargePointId,
    props.plan.id,
  ),
);

const removeScheduledChargingPlan = (planId) => {
  mqttStore.removeScheduledChargingPlanForChargePoint(
    props.chargePointId,
    planId,
  );
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
