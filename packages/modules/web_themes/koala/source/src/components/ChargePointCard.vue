<template>
  <q-card ref="cardRef" class="full-height card-width">
    <q-card-section>
      <div class="row items-center text-h6 text-bold">
        <div class="col flex items-center">
          {{ name }}
          <ChargePointLock :charge-point-id="props.chargePointId" />
          <ChargePointStateIcon
            :charge-point-id="Number(props.chargePointId)"
          />
          <ChargePointTimeCharging
            :charge-point-id="Number(props.chargePointId)"
            :readonly="true"
            :iconSize="'xs'"
            :toolTip="true"
          />
        </div>
        <q-icon
          class="cursor-pointer"
          name="settings"
          size="sm"
          @click="settingsVisible = true"
        />
      </div>
      <ChargePointFaultMessage :charge-point-id="props.chargePointId" />
      <ChargePointStateMessage :charge-point-id="props.chargePointId" />
      <div class="row items-center q-mt-sm">
        <ChargePointVehicleSelect
          :charge-point-id="Number(props.chargePointId)"
        />
        <ChargePointPriority :charge-point-id="props.chargePointId" />
      </div>
      <ChargePointModeButtons :charge-point-id="props.chargePointId" />
      <div class="row q-mt-sm">
        <div class="col">
          <div class="text-subtitle2">Leistung</div>
          <div class="col no-wrap">
            <ChargePointPowerData
              :power="power"
              :phase-number="phaseNumber"
              :current="chargingCurrent"
            />
          </div>
        </div>
        <div class="col text-right">
          <div class="text-subtitle2">geladen</div>
          {{ energyChargedPlugged }}
        </div>
      </div>
      <SliderDouble
        v-if="showSocTargetSlider"
        class="q-mt-sm"
        :model-value="target"
        :readonly="true"
        :charge-mode="chargeMode"
        :limit-mode="limitMode"
        :current-value="currentValue"
        :target-time="vehicleTarget.time"
      >
        <template #update-soc-icon>
          <q-icon
            v-if="vehicleSocType === 'manual' && limitMode !== 'amount'"
            name="edit"
            size="xs"
            class="q-ml-xs cursor-pointer"
            @click="socInputVisible = true"
          >
            <q-tooltip>SoC eingeben</q-tooltip>
          </q-icon>
          <q-icon
            v-else-if="vehicleSocType !== undefined && limitMode !== 'amount'"
            name="refresh"
            size="xs"
            class="q-ml-xs cursor-pointer"
            @click="refreshSoc"
          >
            <q-tooltip>SoC aktualisieren</q-tooltip>
          </q-icon>
        </template>
      </SliderDouble>
      <slot name="card-footer"></slot>
    </q-card-section>
  </q-card>
  <!-- //////////////////////  Settings popup dialog   //////////////////// -->
  <ChargePointSettings
    :chargePointId="props.chargePointId"
    v-model="settingsVisible"
  />
  <ManualSocDialog
    :vehicleId="vehicleId"
    :chargePointId="props.chargePointId"
    v-model:socDialogVisible="socInputVisible"
  />
</template>
<script setup lang="ts">
import { computed, ref, onMounted, inject } from 'vue';
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
import ManualSocDialog from './ManualSocDialog.vue';
import ChargePointTimeCharging from './ChargePointTimeCharging.vue';
import ChargePointPowerData from './ChargePointPowerData.vue';
import { useQuasar } from 'quasar';

const cardRef = ref<{ $el: HTMLElement } | null>(null);
const setCardWidth =
  inject<(width: number | undefined) => void>('setCardWidth');

const mqttStore = useMqttStore();

const $q = useQuasar();

const props = defineProps<{
  chargePointId: number;
}>();

const vehicleId = computed(() => {
  return mqttStore.chargePointConnectedVehicleInfo(props.chargePointId).value
    ?.id;
});

const limitMode = computed(() => {
  switch (chargeMode.value) {
    case 'instant_charging':
      return mqttStore.chargePointConnectedVehicleInstantChargeLimit(
        props.chargePointId,
      ).value;
    case 'pv_charging':
      return mqttStore.chargePointConnectedVehiclePvChargeLimit(
        props.chargePointId,
      ).value;
    case 'eco_charging':
      return mqttStore.chargePointConnectedVehicleEcoChargeLimit(
        props.chargePointId,
      ).value;
    case 'scheduled_charging':
      return vehicleTarget.value.limit_mode;
    default:
      return 'soc';
  }
});

const settingsVisible = ref<boolean>(false);

const socInputVisible = ref<boolean>(false);
const name = computed(() => mqttStore.chargePointName(props.chargePointId));
// Typecast to string is better here because the store method returns a union type which
// would need to be repeated in child component ChargePointPowerData
// unnecessary as parameter returnType: string = 'textValue' is already set as default in store
const power = computed(
  () => mqttStore.chargePointPower(props.chargePointId) as string,
);

const energyChargedPlugged = computed(() =>
  mqttStore.chargePointEnergyChargedPlugged(props.chargePointId),
);

const phaseNumber = computed(() =>
  mqttStore.chargePointPhaseNumber(props.chargePointId),
);
// Typecast to string is better here because the store method returns a union type which
// would need to be repeated in child component ChargePointPowerData
// unnecessary as parameter returnType: string = 'textValue' is already set as default in store
const chargingCurrent = computed(
  () => mqttStore.chargePointChargingCurrent(props.chargePointId) as string,
);

const currentValue = computed(() => {
  if (limitMode.value === 'amount') {
    return mqttStore.chargePointEnergyChargedPlugged(
      props.chargePointId,
      'value',
    ) as number;
  } else {
    return Math.round(
      mqttStore.chargePointConnectedVehicleSoc(props.chargePointId).value
        ?.soc ?? 0,
    );
  }
});

const chargeMode = computed(
  () =>
    mqttStore.chargePointConnectedVehicleChargeMode(props.chargePointId).value,
);

const target = computed(() => {
  switch (chargeMode.value) {
    case 'scheduled_charging':
      return vehicleTarget.value.limit;
    case 'instant_charging':
      const instantLimitMode =
        mqttStore.chargePointConnectedVehicleInstantChargeLimit(
          props.chargePointId,
        ).value;
      switch (instantLimitMode) {
        case 'soc':
          return (
            mqttStore.chargePointConnectedVehicleInstantChargeLimitSoC(
              props.chargePointId,
            ).value ?? 0
          );
        case 'amount':
          return (
            (mqttStore.chargePointConnectedVehicleInstantChargeLimitEnergy(
              props.chargePointId,
            ).value ?? 0) * 1000
          );
      }
    case 'pv_charging':
      const pvLimitMode = mqttStore.chargePointConnectedVehiclePvChargeLimit(
        props.chargePointId,
      ).value;
      switch (pvLimitMode) {
        case 'soc':
          return (
            mqttStore.chargePointConnectedVehiclePvChargeLimitSoC(
              props.chargePointId,
            ).value ?? 0
          );
        case 'amount':
          return (
            (mqttStore.chargePointConnectedVehiclePvChargeLimitEnergy(
              props.chargePointId,
            ).value ?? 0) * 1000
          );
      }
    case 'eco_charging':
      const ecoLimitMode = mqttStore.chargePointConnectedVehicleEcoChargeLimit(
        props.chargePointId,
      ).value;
      switch (ecoLimitMode) {
        case 'soc':
          return (
            mqttStore.chargePointConnectedVehicleEcoChargeLimitSoC(
              props.chargePointId,
            ).value ?? 0
          );
        case 'amount':
          return (
            (mqttStore.chargePointConnectedVehicleEcoChargeLimitEnergy(
              props.chargePointId,
            ).value ?? 0) * 1000
          );
      }
    default:
      return undefined;
  }
});

const showSocTargetSlider = computed(() => {
  if (target.value && target.value > 999) {
    // we have a energy based target
    return true;
  }
  if (vehicleSocType.value !== undefined) {
    // we have a soc module defined
    return true;
  }
  return false;
});

const vehicleTarget = computed(() => {
  return mqttStore.vehicleChargeTarget(props.chargePointId).value;
});

const vehicleSocType = computed(() =>
  mqttStore.chargePointConnectedVehicleSocType(props.chargePointId),
)?.value;

const refreshSoc = () => {
  mqttStore.chargePointConnectedVehicleForceSocUpdate(props.chargePointId);
  $q.notify({
    type: 'positive',
    message: 'SoC Update angefordert.',
  });
};

onMounted(() => {
  const cardWidth = cardRef.value?.$el.offsetWidth;
  setCardWidth?.(cardWidth);
});
</script>
<style lang="scss" scoped>
.card-width {
  width: 22em;
}
</style>
