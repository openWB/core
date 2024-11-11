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
        <q-icon name="settings" size="sm" @click="settingsVisible = true" />
      </div>
      <ChargePointFaultMessage :charge-point-id="props.chargePointId" />
      <ChargePointStateMessage :charge-point-id="props.chargePointId" />
      <ChargePointModeButtons :charge-point-id="props.chargePointId" />
      <div class="row q-mt-sm">
        <div class="col q-pa-sm">
          <div class="text-subtitle2">Leistung</div>
          {{ power }}
        </div>
        <div class="col q-pa-sm">
          <div class="text-subtitle2">geladen</div>
          {{ energyCharged }}
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
  <ChargePointSettings
    :chargePointId="props.chargePointId"
    v-model="settingsVisible"
  />
</template>

<script setup lang="ts">
import { computed, ref } from 'vue';
import { useMqttStore } from 'src/stores/mqtt-store';
import SliderQuasar from './SliderQuasar.vue';
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
const energyCharged = computed(() =>
  mqttStore.chargePointEnergyCharged(props.chargePointId, 'textValue'),
);
</script>
