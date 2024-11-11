<template>
  <q-dialog
    v-model="visible"
    :maximized="$q.screen.width < 385"
    :backdrop-filter="$q.screen.width < 385 ? '' : 'blur(4px)'"
  >
    <q-card>
      <q-card-section>
        <div class="text-h6">Einstellungen {{ name }}</div>
      </q-card-section>

      <q-card-section class="q-pt-none">
        <div class="row items-center q-ma-none q-pa-none">
          <div>
            <div class="text-subtitle2 q-mr-sm">Fahrzeug</div>
          </div>
          <ChargePointVehicleSelect
            :charge-point-id="props.chargePointId"
            :readonly="false"
          />
        </div>
        <div class="row items-center q-ma-none q-pa-none no-wrap">
          <ChargePointModeButtons :charge-point-id="props.chargePointId" />
        </div>
        <div class="row items-center q-ma-none q-pa-none no-wrap">
          <div class="text-subtitle2 q-mr-sm">Sperren</div>
          <div>
            <ChargePointLock :charge-point-id="props.chargePointId" />
          </div>
        </div>

        <div class="row items-center q-ma-none q-pa-none no-wrap">
          <div class="text-subtitle2 q-mr-sm">Priorität</div>
          <div>
            <ChargePointPriority
              :charge-point-id="props.chargePointId"
              :readonly="false"
            />
          </div>
        </div>

        <!-- ///////////////// Instant charge settings /////////////////// -->
        <div v-if="chargeMode.value === 'instant_charging'">
          <SliderStandard
            title="Stromstärke"
            :min="6"
            :max="32"
            unit="A"
            v-model="instantChargeCurrent.value"
            class="q-mt-sm"
          />
          <!-- <SliderQuasar class="q-mt-sm" :readonly="false" /> -->
          <div class="text-subtitle2 q-mr-sm">Begrenzung</div>
          <ChargePointLimitSettings :charge-point-id="props.chargePointId" />
        </div>

        <!-- ///////////////// PV charge settings /////////////////// -->
        <div v-if="chargeMode.value === 'pv_charging'">
          <SliderStandard
            title="Minimaler Dauerstrom"
            :min="0"
            :max="16"
            unit="A"
            v-model="pvMinCurrent.value"
            class="q-mt-md"
          />

          <SliderStandard
            title="Mindest-SoC für das Fahrzeug"
            :min="0"
            :max="95"
            :step="5"
            unit="%"
            v-model="pvMinSoc.value"
            class="q-mt-md"
          />

          <SliderStandard
            title="Mindest-SoC-Strom"
            :min="6"
            :max="32"
            unit="A"
            v-model="pvMinSocCurrent.value"
            class="q-mt-md"
          />

          <SliderStandard
            title="SoC-Limit für das Fahrzeug"
            :min="0"
            :max="100"
            :step="5"
            unit="%"
            v-model="pvMaxSocLimit.value"
            class="q-mt-md"
          />

          <div class="row items-center q-ma-none q-pa-none no-wrap">
            <div class="text-subtitle2 q-mr-sm">Einspeisegrenze beachten</div>
            <div>
              <ToggleStandard v-model="feedInLimit.value" />
            </div>
          </div>
        </div>
      </q-card-section>
      <q-card-actions align="right">
        <q-btn flat label="OK" color="primary" v-close-popup />
      </q-card-actions>
    </q-card>
  </q-dialog>
</template>

<script setup lang="ts">
import { useQuasar } from 'quasar';
import { useMqttStore } from 'src/stores/mqtt-store';
import { computed, ref, watch } from 'vue';
import ToggleStandard from './ToggleStandard.vue';
import ChargePointLimitSettings from './ChargePointLimitSettings.vue';
import SliderStandard from './SliderStandard.vue';
import ChargePointPriority from './ChargePointPriority.vue';
import ChargePointLock from './ChargePointLock.vue';
import ChargePointModeButtons from './ChargePointModeButtons.vue';
import ChargePointVehicleSelect from './ChargePointVehicleSelect.vue';

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

const instantChargeCurrent = computed(() =>
  mqttStore.chargePointConnectedVehicleInstantChargeCurrent(
    props.chargePointId,
  ),
);

const pvMinCurrent = computed(() =>
  mqttStore.chargePointConnectedVehiclePVChargeMinCurrent(props.chargePointId),
);

const pvMinSoc = computed(() =>
  mqttStore.chargePointConnectedVehiclePVChargeMinSoc(props.chargePointId),
);

const pvMinSocCurrent = computed(() =>
  mqttStore.chargePointConnectedVehiclePVChargeMinSocCurrent(
    props.chargePointId,
  ),
);

const pvMaxSocLimit = computed(() =>
  mqttStore.chargePointConnectedVehiclePVChargeMaxSoc(props.chargePointId),
);

const feedInLimit = computed(() =>
  mqttStore.chargePointConnectedVehiclePVChargeFeedInLimit(props.chargePointId),
);
</script>
