<template>
  <q-card class="rounded-borders-md card-width">
    <q-card-section>
      <div class="row no-wrap">
        <div class="text-h6 ellipsis" :title="planName.value">
          {{ planName.value }}
        </div>
        <q-space />
        <q-btn icon="close" flat round dense v-close-popup />
      </div>
      <BaseMessage
        :show-message="isTemporaryPlan"
        message="Temporärer Plan. Der Plan wird nach dem Abstecken verworfen."
        type="warning"
      />

      <BaseMessage
        :show-message="temporaryChargeModeActive"
        message="Temporärer Modus aktiv. Alle Planänderungen werden nach dem Abstecken verworfen."
        type="warning"
      />
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
        v-if="acChargingEnabled"
        class="q-mb-sm"
        title="Ladestrom"
        :min="6"
        :max="32"
        unit="A"
        v-model="planCurrent.value"
      />
      <q-input
        v-if="dcChargingEnabled"
        v-model="planDcPower.value"
        label="Ladeleistung (DC)"
        class="col q-mb-sm"
      >
        <template v-slot:append>
          <div class="text-body2">kW</div>
        </template>
      </q-input>
      <div v-if="acChargingEnabled">
        <div class="text-subtitle2 q-mr-sm">Anzahl Phasen</div>
        <div
          class="row items-center justify-center q-ma-none q-pa-none no-wrap"
        >
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
      <div v-if="temporaryChargeModeActive" class="row q-mt-lg">
        <q-btn
          size="sm"
          class="col"
          color="warning"
          :href="`/openWB/web/settings/#/VehicleConfiguration/charge_template/${chargeTemplateId ?? ''}`"
          ><q-icon left size="xs" name="settings" /> Ladeplan
          Einstellungen</q-btn
        >
      </div>
      <div class="row q-mt-md">
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
import BaseMessage from './BaseMessage.vue';
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

const planDcPower = computed(() =>
  mqttStore.vehicleTimeChargingPlanDcPower(props.chargePointId, props.plan.id),
);

const dcChargingEnabled = computed(
  () => mqttStore.chargePointChargeType(props.chargePointId).value === 'DC',
);

const acChargingEnabled = computed(
  () => mqttStore.chargePointChargeType(props.chargePointId).value === 'AC',
);

const PermanentTimeChargingPlansIds = computed(() =>
  mqttStore
    .vehicleTimeChargingPlansPermanent(props.chargePointId)
    .map((plan) => plan.id),
);

const isTemporaryPlan = computed(
  () => !PermanentTimeChargingPlansIds.value.includes(props.plan.id),
);

const temporaryChargeModeActive = computed(
  () => mqttStore.temporaryChargeModeAktiv ?? false,
);

const chargeTemplateId = computed(
  () =>
    mqttStore.chargePointConnectedVehicleChargeTemplate(props.chargePointId)
      .value?.id,
);

const removeTimeChargingPlan = (planId: number) => {
  mqttStore.removeTimeChargingPlanForChargePoint(props.chargePointId, planId);
  emit('close');
};
</script>

<style scoped>
.card-width {
  width: 26em;
}

.q-btn-group .q-btn {
  min-width: 100px !important;
  font-size: 10px !important;
}

.flex-grow {
  flex-grow: 1;
}
</style>
