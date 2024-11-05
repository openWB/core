<template>
  <q-card class="full-height" style="max-width: 24em">
    <q-card-section>
      <div class="row items-center text-h6" style="font-weight: bold">
        <div class="col">
          {{ name }}
        </div>
        <ChargePointLock
          :charge-point-id="props.chargePointId"
          :readonly="true"
        />
        <ChargePointStateIcon :charge-point-id="props.chargePointId" />
        <q-icon name="settings" size="sm" @click="settings = true" />
      </div>
      <ChargePointFaultMessage :charge-point-id="props.chargePointId" />
      <ChargePointStateMessage :charge-point-id="props.chargePointId" />
      <ChargePointModeButtons :charge-point-id="props.chargePointId" />
      <div class="row q-mt-sm">
        <div class="q-pa-sm">
          <div class="text-subtitle2">Leistung</div>
          {{ power }}
        </div>
        <div class="q-pa-sm">
          <div class="text-subtitle2">geladen</div>
          {{ charged }}
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
      <SliderQuasar class="q-mt-sm" :readonly="true" />
    </q-card-section>
  </q-card>

  <!-- //////////////////////  Settings popup dialog  //////////////////// -->

  <q-dialog v-model="settings" :backdrop-filter="'blur(4px)'">
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

        <SliderStandard
          v-if="chargeMode === 'instant_charging'"
          :title="'Stromstärke'"
          :min="6"
          :max="32"
          :units="'A'"
          :value="instantChargeCurrent"
          @update:value="updateInstantChargeCurrent"
          class="q-mt-sm"
        />
        <!-- <SliderQuasar class="q-mt-sm" :readonly="false" /> -->
        <div
          v-if="chargeMode === 'instant_charging'"
          class="text-subtitle2 q-mr-sm"
        >
          Begrenzung
        </div>
        <div
          v-if="chargeMode === 'instant_charging'"
          class="row items-center justify-center q-ma-none q-pa-none no-wrap"
        >
          <ChargePointLimitButtons :charge-point-id="props.chargePointId" />
        </div>
        <SliderStandard
          v-if="chargeMode === 'instant_charging' && limitMode === 'soc'"
          :title="'SoC-Limit für das Fahrzeug'"
          :min="5"
          :max="100"
          :step="5"
          :units="'%'"
          :value="instantSoC"
          @update:value="updateInstantSoC"
          class="q-mt-md"
        />
        <SliderStandard
          v-if="chargeMode === 'instant_charging' && limitMode === 'amount'"
          :title="'Energie-Limit'"
          :min="1"
          :max="50"
          :units="'kWh'"
          :value="instantEnergy"
          @update:value="updateInstantEnergy"
          class="q-mt-md"
        />

        <!-- ///////////////// PV charge settings /////////////////// -->

        <SliderStandard
          v-if="chargeMode === 'pv_charging'"
          :title="'Minimaler Dauerstrom'"
          :min="0"
          :max="16"
          :units="'A'"
          :value="pvMinCurrent"
          @update:value="updatePvMinCurrent"
          class="q-mt-md"
        />

        <SliderStandard
          v-if="chargeMode === 'pv_charging'"
          :title="'Mindest-SoC für das Fahrzeug'"
          :min="0"
          :max="95"
          :step="5"
          :units="'%'"
          :value="pvMinSoc"
          @update:value="updatePvMinSoc"
          class="q-mt-md"
        />

        <SliderStandard
          v-if="chargeMode === 'pv_charging'"
          :title="'Mindest-SoC-Strom'"
          :min="6"
          :max="32"
          :units="'A'"
          :value="pvMinSocCurrent"
          @update:value="updatePvMinSocCurrent"
          class="q-mt-md"
        />

        <SliderStandard
          v-if="chargeMode === 'pv_charging'"
          :title="'SoC-Limit für das Fahrzeug'"
          :min="0"
          :max="100"
          :step="5"
          :units="'%'"
          :value="pvMaxSocLimit"
          @update:value="updatePvMaxSocLimit"
          class="q-mt-md"
        />

        <div
          v-if="chargeMode === 'pv_charging'"
          class="row items-center q-ma-none q-pa-none no-wrap"
        >
          <div class="text-subtitle2 q-mr-sm">Einspeisegrenze beachten</div>
          <div>
            <ToggleStandard
              :value="feedInlimit"
              @update:value="updateFeedInLimit"
            />
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
import { computed, ref } from 'vue';
import SliderQuasar from './SliderQuasar.vue';
import SliderStandard from './SliderStandard.vue';
import { useMqttStore } from 'src/stores/mqtt-store';
import ChargePointLock from './ChargePointLock.vue';
import ToggleStandard from './ToggleStandard.vue';
import ChargePointStateIcon from './ChargePointStateIcon.vue';
import ChargePointPriority from './ChargePointPriority.vue';
import ChargePointModeButtons from './ChargePointModeButtons.vue';
import ChargePointLimitButtons from './ChargePointLimitButtons.vue';
import ChargePointStateMessage from './ChargePointStateMessage.vue';
import ChargePointFaultMessage from './ChargePointFaultMessage.vue';
import ChargePointVehicleSelect from './ChargePointVehicleSelect.vue';

const props = defineProps<{
  chargePointId: number;
}>();

const mqttStore = useMqttStore();

const settings = ref<boolean>(false);
const name = computed(() => mqttStore.chargePointName(props.chargePointId));
const power = computed(() =>
  mqttStore.chargePointPower(props.chargePointId, 'textValue'),
);
const chargeMode = computed(
  () =>
    mqttStore.chargePointConnectedVehicleChargeMode(props.chargePointId)?.value,
);

const instantChargeCurrent = computed(
  () =>
    mqttStore.chargePointConnectedVehicleInstantChargeCurrent(
      props.chargePointId,
    )?.value,
);

const updateInstantChargeCurrent = (newValue: number) => {
  mqttStore.chargePointConnectedVehicleInstantChargeCurrent(
    props.chargePointId,
  ).value = newValue;
};

const limitMode = computed(
  () =>
    mqttStore.chargePointConnectedVehicleInstantChargeLimit(props.chargePointId)
      ?.value,
);

const instantSoC = computed(
  () =>
    mqttStore.chargePointConnectedVehicleInstantChargeLimitSoC(
      props.chargePointId,
    )?.value,
);

const updateInstantSoC = (newValue: number) => {
  mqttStore.chargePointConnectedVehicleInstantChargeLimitSoC(
    props.chargePointId,
  ).value = newValue;
};

const instantEnergy = computed(
  () =>
    mqttStore.chargePointConnectedVehicleInstantChargeEnergieLimit(
      props.chargePointId,
    )?.value,
);

const updateInstantEnergy = (newValue: number) => {
  mqttStore.chargePointConnectedVehicleInstantChargeEnergieLimit(
    props.chargePointId,
  ).value = newValue;
};

const pvMinCurrent = computed(
  () =>
    mqttStore.chargePointConnectedVehiclePVChargeMinCurrent(props.chargePointId)
      ?.value,
);

const updatePvMinCurrent = (newValue: number) => {
  mqttStore.chargePointConnectedVehiclePVChargeMinCurrent(
    props.chargePointId,
  ).value = newValue;
};

const pvMinSoc = computed(
  () =>
    mqttStore.chargePointConnectedVehiclePVChargeMinSoc(props.chargePointId)
      ?.value,
);

const updatePvMinSoc = (newValue: number) => {
  mqttStore.chargePointConnectedVehiclePVChargeMinSoc(
    props.chargePointId,
  ).value = newValue;
};

const pvMinSocCurrent = computed(
  () =>
    mqttStore.chargePointConnectedVehiclePVChargeMinSocCurrent(
      props.chargePointId,
    )?.value,
);

const updatePvMinSocCurrent = (newValue: number) => {
  mqttStore.chargePointConnectedVehiclePVChargeMinSocCurrent(
    props.chargePointId,
  ).value = newValue;
};

const pvMaxSocLimit = computed(
  () =>
    mqttStore.chargePointConnectedVehiclePVChargeMaxSoc(props.chargePointId)
      ?.value,
);

const updatePvMaxSocLimit = (newValue: number) => {
  mqttStore.chargePointConnectedVehiclePVChargeMaxSoc(
    props.chargePointId,
  ).value = newValue;
};

const feedInlimit = computed(
  () =>
    mqttStore.chargePointConnectedVehiclePVChargeFeedInLimit(
      props.chargePointId,
    )?.value,
);

const updateFeedInLimit = (newValue: boolean) => {
  mqttStore.chargePointConnectedVehiclePVChargeFeedInLimit(
    props.chargePointId,
  ).value = newValue;
};

// Begin dummy data
const charged = ref<string>('12,3 kWh');
// End dummy data
</script>
