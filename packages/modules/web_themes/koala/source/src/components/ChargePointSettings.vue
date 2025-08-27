<template>
  <q-dialog
    v-model="visible"
    :maximized="isSmallScreen"
    :backdrop-filter="isSmallScreen ? '' : 'blur(4px)'"
  >
    <q-card>
      <q-card-section>
        <div class="row no-wrap">
          <div class="text-h6 q-pr-sm">Einstellungen:</div>
          <div class="text-h6 ellipsis" :title="name">{{ name }}</div>
          <q-space />
          <q-btn icon="close" flat round dense v-close-popup />
        </div>
      </q-card-section>
      <q-separator />
      <q-card-section>
        <div class="row items-center justify-between">
          <div class="text-subtitle2">Ladepunkt sperren</div>
          <ChargePointLock :charge-point-id="props.chargePointId" dense />
        </div>
        <q-separator class="q-mt-sm" />
        <div class="row items-center q-mt-sm">
          <div class="col-auto text-subtitle2 q-mr-sm">Fahrzeug</div>
          <div class="col">
            <ChargePointVehicleSelect
              class="full-width"
              :charge-point-id="props.chargePointId"
              :readonly="false"
            />
          </div>
        </div>
        <div class="row items-center justify-between q-mt-sm">
          <div class="text-subtitle2">Priorität</div>
          <ChargePointPriority
            :charge-point-id="props.chargePointId"
            :readonly="false"
            dense
          />
        </div>
        <q-separator class="q-mt-sm" />
        <div class="row items-center no-wrap">
          <ChargePointModeButtons :charge-point-id="props.chargePointId" />
        </div>
        <!-- ///////////////// Instant charge settings /////////////////// -->
        <div v-if="chargeMode.value === 'instant_charging'">
          <ChargePointInstantSettings :charge-point-id="props.chargePointId" />
        </div>
        <!-- ///////////////// Pv charge settings /////////////////// -->
        <div v-if="chargeMode.value === 'pv_charging'">
          <ChargePointPvSettings :charge-point-id="props.chargePointId" />
        </div>
        <!-- ///////////////// Eco charge settings /////////////////// -->
        <div v-if="chargeMode.value === 'eco_charging'">
          <ChargePointEcoSettings :charge-point-id="props.chargePointId" />
        </div>
        <!-- /////////////////  scheduled charging settings /////////////////// -->
        <div v-if="chargeMode.value === 'scheduled_charging'">
          <ChargePointScheduledSettings
            :charge-point-id="props.chargePointId"
          />
        </div>
        <!-- /////////////////  time charging settings /////////////////// -->
        <div v-if="chargeMode.value !== 'stop'">
          <q-separator class="q-my-sm" />
          <ChargePointTimeChargingSettings
            :charge-point-id="props.chargePointId"
          />
        </div>
      </q-card-section>
    </q-card>
  </q-dialog>
</template>

<script setup lang="ts">
import { Screen, QDialog } from 'quasar';
import { useMqttStore } from 'src/stores/mqtt-store';
import { computed, ref, watch } from 'vue';
import ChargePointInstantSettings from './ChargePointInstantSettings.vue';
import ChargePointPvSettings from './ChargePointPvSettings.vue';
import ChargePointEcoSettings from './ChargePointEcoSettings.vue';
import ChargePointScheduledSettings from './ChargePointScheduledSettings.vue';
import ChargePointTimeChargingSettings from './ChargePointTimeChargingSettings.vue';
import ChargePointPriority from './ChargePointPriority.vue';
import ChargePointLock from './ChargePointLock.vue';
import ChargePointModeButtons from './ChargePointModeButtons.vue';
import ChargePointVehicleSelect from './ChargePointVehicleSelect.vue';

const mqttStore = useMqttStore();

const props = defineProps<{
  chargePointId: number;
  modelValue: boolean;
}>();

const emit = defineEmits<{
  'update:model-value': [value: boolean];
}>();

const isSmallScreen = computed(() => Screen.lt.sm);

const tempValue = ref<boolean>(props.modelValue);

watch(
  () => props.modelValue,
  (value) => {
    tempValue.value = value;
  },
);

const visible = computed({
  get: () => tempValue.value,
  set: (value) => {
    tempValue.value = value;
    emit('update:model-value', value);
  },
});

const name = computed(() => mqttStore.chargePointName(props.chargePointId));

const chargeMode = computed(() =>
  mqttStore.chargePointConnectedVehicleChargeMode(props.chargePointId),
);
</script>
