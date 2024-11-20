<template>
  <q-card class="rounded-borders-md">
    <q-card-section>
      <div class="row items-center q-mb-sm">
        <q-input
          v-model="planName(plan.id).value"
          label="Plan Name"
          class="col"
        />
      </div>
      <div class="row items-center q-mb-md">
        <div class="text-subtitle2 q-mr-sm">Aktiv</div>
        <ToggleStandard
          :model-value="plan.active"
          @update:model-value="togglePlanActive(plan.id)"
          :size="'sm'"
          color="positive"
        />
      </div>
      <div class="row items-center q-mb-md">
        <q-input
          v-model="planTime(plan.id).value"
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
        v-model="planCurrent(plan.id).value"
      />
      <q-btn-group>
        <q-btn
          size="sm"
          :color="
            planLimitSelected(plan.id).value === 'soc' ? 'primary' : 'grey'
          "
          @click="planLimitSelected(plan.id).value = 'soc'"
          label="SoC"
        />
        <q-btn
          size="sm"
          :color="
            planLimitSelected(plan.id).value === 'amount' ? 'primary' : 'grey'
          "
          @click="planLimitSelected(plan.id).value = 'amount'"
          label="Amount"
        />
      </q-btn-group>
      <div v-if="planLimitSelected(plan.id).value === 'soc'" class="q-mt-md">
        <SliderStandard
          title="Fahrzeug-SoC zum Zielzeitpunkt"
          :min="0"
          :max="100"
          :step="5"
          unit="%"
          v-model="planSocScheduled(plan.id).value"
          class="q-mt-sm"
        />
        <SliderStandard
          title="Fahrzeug-SoC mit Überschuss"
          :min="0"
          :max="100"
          :step="5"
          unit="%"
          v-model="planSocLimit(plan.id).value"
        />
      </div>
      <q-input
        v-if="planLimitSelected(plan.id).value === 'amount'"
        v-model="planLimitAmount(plan.id).value"
        label="Ziel-Energy (kWh)"
        class="col"
      />
      <!-- Inside your expansion item content -->
      <div class="q-mb-md">
        <div class="text-subtitle2 q-mb-sm q-mt-md">Wiederholungen</div>
        <q-btn-group spread>
          <q-btn
            size="sm"
            :color="
              planFrequency(plan.id).value === 'once' ? 'primary' : 'grey'
            "
            @click="planFrequency(plan.id).value = 'once'"
            label="Einmalig"
          />
          <q-btn
            size="sm"
            :color="
              planFrequency(plan.id).value === 'daily' ? 'primary' : 'grey'
            "
            @click="planFrequency(plan.id).value = 'daily'"
            label="Täglich"
          />
          <q-btn
            size="sm"
            :color="
              planFrequency(plan.id).value === 'weekly' ? 'primary' : 'grey'
            "
            @click="planFrequency(plan.id).value = 'weekly'"
            label="Wöchentlich"
          />
        </q-btn-group>

        <!-- Date input for 'once' -->
        <div v-if="planFrequency(plan.id).value === 'once'" class="q-mt-sm">
          <q-input
            v-model="planOnceDate(plan.id).value"
            type="date"
            label="Datum"
          />
        </div>

        <!-- Weekly toggles -->
        <div v-if="planFrequency(plan.id).value === 'weekly'" class="q-mt-sm">
          <!-- First row: Monday-Thursday -->
          <div class="row items-center q-gutter-sm q-mb-sm">
            <div
              v-for="(day, index) in weekDays.slice(0, 5)"
              :key="day"
              class="column items-center"
            >
              <div class="text-caption">{{ day }}</div>
              <ToggleStandard
                v-model="weeklyDaysModel(plan.id).value[index]"
                @update:model-value="updateWeeklyDays(plan.id)"
                color="positive"
                :size="'sm'"
              />
            </div>
          </div>

          <!-- Second row: Friday-Sunday -->
          <div class="row items-center q-gutter-sm">
            <div
              v-for="(day, index) in weekDays.slice(5)"
              :key="day"
              class="column items-center"
            >
              <div class="text-caption">{{ day }}</div>
              <ToggleStandard
                v-model="weeklyDaysModel(plan.id).value[index + 5]"
                @update:model-value="updateWeeklyDays(plan.id)"
                color="positive"
                :size="'sm'"
              />
            </div>
          </div>
        </div>
      </div>
    </q-card-section>
  </q-card>
</template>

<script setup lang="ts">
import { useMqttStore } from 'src/stores/mqtt-store';
import SliderStandard from './SliderStandard.vue';
import ToggleStandard from './ToggleStandard.vue';
import { Ref, ref } from 'vue';
import { type ScheduledChargingPlan } from '../stores/mqtt-store-model';

const props = defineProps<{
  chargePointId: number;
  plan: ScheduledChargingPlan;
}>();

const mqttStore = useMqttStore();

const weekDays = ['Mo', 'Di', 'Mi', 'Do', 'Fr', 'Sa', 'So'];

const togglePlanActive = (planId: string) =>
  mqttStore.vehicleToggleScheduledChargingPlanActive(
    props.chargePointId,
    planId,
  );

const planCurrent = (planId: string) =>
  mqttStore.vehicleScheduledChargingPlanCurrent(props.chargePointId, planId);

const planLimitSelected = (planId: string) =>
  mqttStore.vehicleScheduledChargingPlanLimitSelected(
    props.chargePointId,
    planId,
  );

const planLimitAmount = (planId: string) =>
  mqttStore.vehicleScheduledChargingPlanEnergyAmount(
    props.chargePointId,
    planId,
  );

const planName = (planId: string) =>
  mqttStore.vehicleScheduledChargingPlanName(props.chargePointId, planId);

const planTime = (planId: string) =>
  mqttStore.vehicleScheduledChargingPlanTime(props.chargePointId, planId);

const planFrequency = (planId: string) =>
  mqttStore.vehicleScheduledChargingPlanFrequencySelected(
    props.chargePointId,
    planId,
  );

const planOnceDate = (planId: string) =>
  mqttStore.vehicleScheduledChargingPlanOnceDate(props.chargePointId, planId);

const weeklyDaysModel = (planId: string): Ref<boolean[]> =>
  ref(
    mqttStore.vehicleScheduledChargingPlanWeeklyDays(
      props.chargePointId,
      planId,
    ).value || Array(7).fill(false),
  );

const updateWeeklyDays = (planId: string) => {
  mqttStore.vehicleScheduledChargingPlanWeeklyDays(
    props.chargePointId,
    planId,
  ).value = weeklyDaysModel(planId).value;
};

const planSocLimit = (planId: string) =>
  mqttStore.vehicleScheduledChargingPlanSocLimit(props.chargePointId, planId);

const planSocScheduled = (planId: string) =>
  mqttStore.vehicleScheduledChargingPlanSocScheduled(
    props.chargePointId,
    planId,
  );
</script>
