<template>
  <q-dialog
    v-model="visible"
    :maximized="$q.platform.is.mobile"
    :backdrop-filter="$q.screen.width < 385 ? '' : 'blur(4px)'"
  >
    <q-card>
      <q-card-section>
        <div class="row">
          <div class="text-h6">Einstellungen {{ name }}</div>
          <q-space />
          <q-btn icon="close" flat round dense v-close-popup />
        </div>
      </q-card-section>
      <q-card-section class="q-py-none">
        <div class="row items-center no-wrap">
          <div class="col text-subtitle2">Ladepunkt sperren</div>
          <div class="col">
            <ChargePointLock :charge-point-id="props.chargePointId" dense />
          </div>
        </div>
        <q-separator class="q-mt-sm"/>
        <div class="row items-center q-mt-sm">
          <div>
            <div class="text-subtitle2 q-mr-sm">Fahrzeug</div>
          </div>
          <ChargePointVehicleSelect
            :charge-point-id="props.chargePointId"
            :readonly="false"
          />
        </div>
        <div class="row items-center no-wrap q-mt-sm">
          <div class="col row items-center">
            <div class="col text-subtitle2">Priorität</div>
            <div class="col">
              <ChargePointPriority
                :charge-point-id="props.chargePointId"
                :readonly="false"
                dense
              />
            </div>
          </div>
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
          <ChargePointTimeChargingPlans :charge-point-id="props.chargePointId" />
        </div>
      </q-card-section>
      <q-card-actions align="right">
        <q-btn flat label="OK" color="primary" v-close-popup />
      </q-card-actions>
    </q-card>
  </q-dialog>
</template>

<script setup lang="ts">
import { useQuasar, QDialog } from 'quasar';
import { useMqttStore } from 'src/stores/mqtt-store';
import { computed, ref, watch } from 'vue';
import ChargePointInstantSettings from './ChargePointInstantSettings.vue';
import ChargePointPvSettings from './ChargePointPvSettings.vue';
import ChargePointEcoSettings from './ChargePointEcoSettings.vue';
import ChargePointScheduledSettings from './ChargePointScheduledSettings.vue';
import ChargePointPriority from './ChargePointPriority.vue';
// import ChargePointTimeCharging from './ChargePointTimeCharging.vue';
import ChargePointLock from './ChargePointLock.vue';
import ChargePointModeButtons from './ChargePointModeButtons.vue';
import ChargePointVehicleSelect from './ChargePointVehicleSelect.vue';
import ChargePointTimeChargingPlans from './ChargePointTimeChargingPlans.vue';

const $q = useQuasar();
const mqttStore = useMqttStore();

const props = defineProps<{
  chargePointId: number;
  modelValue: boolean;
}>();

const emit = defineEmits<{
  'update:model-value': [value: boolean];
}>();

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
