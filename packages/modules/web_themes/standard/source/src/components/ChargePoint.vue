<template>
  <q-card class="full-height">
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
        <SliderQuasar class="q-mt-sm" :readonly="false" />
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
import { useMqttStore } from 'src/stores/mqtt-store';
import ChargePointLock from './ChargePointLock.vue';
import ChargePointStateIcon from './ChargePointStateIcon.vue';
import ChargePointPriority from './ChargePointPriority.vue';
import ChargePointModeButtons from './ChargePointModeButtons.vue';
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

// Begin dummy data
const charged = ref<string>('12,3 kWh');
// End dummy data
</script>
