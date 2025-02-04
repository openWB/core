<template>
  <q-card class="full-height card-width">
    <q-card-section>
      <div class="row items-center text-h6 text-bold">
        <div class="col">
          {{ name }}
          <ChargePointLock
            :charge-point-id="props.chargePointId"
            :readonly="true"
          />
          <ChargePointStateIcon :charge-point-id="props.chargePointId" />
        </div>
        <q-icon name="settings" size="sm" @click="settingsVisible = true" />
      </div>
      <ChargePointFaultMessage :charge-point-id="props.chargePointId" />
      <ChargePointStateMessage :charge-point-id="props.chargePointId" />
      <ChargePointModeButtons :charge-point-id="props.chargePointId" />
      <div class="row q-mt-sm">
        <div class="col q-pa-sm">
          <div class="text-subtitle2">Leistung</div>
          {{ power }}
          <q-badge rounded color="primary" :label="phaseNumber">
            <q-tooltip class="bg-primary">Phasenanzahl</q-tooltip>
          </q-badge>
          {{ chargingCurrent + ' A' }}
        </div>
        <div class="col q-pa-sm">
          <div class="text-subtitle2">geladen</div>
          <!-- {{ energyCharged }} -->
          {{ energyChargedPlugged }}
        </div>
      </div>
      <div class="row items-center q-mt-sm">
        <q-icon name="directions_car" size="sm" />
        <ChargePointVehicleSelect
          :charge-point-id="props.chargePointId"
          :readonly="true"
        />
        <ChargePointPriority
          :charge-point-id="props.chargePointId"
          :readonly="true"
        />
      </div>
      <SliderDouble
        v-if="showSocTargetSlider"
        class="q-mt-sm"
        :readonly="true"
        :charge-mode="chargeMode"
        :connected-vehicle-soc="connectedVehicleSoc"
        :target-soc="targetSoc"
        :target-time="targetTime"
      />
    </q-card-section>
  </q-card>

  <!-- //////////////////////  Settings popup dialog   //////////////////// -->
  <ChargePointSettings
    :chargePointId="props.chargePointId"
    v-model="settingsVisible"
  />
</template>

<script setup lang="ts">
import { computed, ref } from 'vue';
import { useMqttStore } from 'src/stores/mqtt-store';
import SliderDouble from './SliderDouble.vue';
import ChargePointLock from './ChargePointLock.vue';
import ChargePointStateIcon from './ChargePointStateIcon.vue';
import ChargePointPriority from './ChargePointPriority.vue';
import ChargePointModeButtons from './ChargePointModeButtons.vue';
import ChargePointStateMessage from './ChargePointStateMessage.vue';
import ChargePointFaultMessage from './ChargePointFaultMessage.vue';
import ChargePointVehicleSelect from './ChargePointVehicleSelect.vue';
import ChargePointSettings from './ChargePointSettings.vue';

const mqttStore = useMqttStore();

const props = defineProps<{
  chargePointId: number;
}>();

const settingsVisible = ref<boolean>(false);
const name = computed(() => mqttStore.chargePointName(props.chargePointId));
const power = computed(() =>
  mqttStore.chargePointPower(props.chargePointId, 'textValue'),
);

const energyChargedPlugged = computed(() =>
  mqttStore.chargePointEnergyChargedPlugged(props.chargePointId, 'textValue'),
);
const phaseNumber = computed(() =>
  mqttStore.chargePointPhaseNumber(props.chargePointId),
);
const chargingCurrent = computed(() =>
  mqttStore.chargePointChargingCurrent(props.chargePointId),
);

const connectedVehicleSoc = computed(() =>
  Math.round(
    mqttStore.chargePointConnectedVehicleSoc(props.chargePointId).value?.soc ??
      0,
  ),
);

const chargeMode = computed(
  () =>
    mqttStore.chargePointConnectedVehicleChargeMode(props.chargePointId).value,
);

const targetSoc = computed<number | undefined>(() => {
  const instantLimitMode =
    mqttStore.chargePointConnectedVehicleInstantChargeLimit(
      props.chargePointId,
    ).value;
  switch (chargeMode.value) {
    case 'scheduled_charging':
      return mqttStore.vehicleScheduledChargingTarget(props.chargePointId).value
        ?.soc;
    case 'instant_charging':
      return instantLimitMode === 'soc'
        ? mqttStore.chargePointConnectedVehicleInstantChargeLimitSoC(
            props.chargePointId,
          ).value
        : undefined;
    case 'pv_charging':
      return mqttStore.chargePointConnectedVehiclePVChargeMaxSoc(
        props.chargePointId,
      ).value;
    default:
      return undefined;
  }
});

const showSocTargetSlider = computed(() => {
  return (
    chargeMode.value !== undefined &&
    !['stop', 'standby'].includes(chargeMode.value)
  );
});

const targetTime = computed(() => {
  const target = mqttStore.vehicleScheduledChargingTarget(
    props.chargePointId,
  ).value;
  if (!target || !target.time || chargeMode.value !== 'scheduled_charging') {
    return 'keine';
  }
  return target.time;
});
</script>

<style lang="scss" scoped>
.card-width {
  max-width: 24em;
}
</style>
