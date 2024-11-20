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
        <div class="row items-center q-ma-none q-pa-none no-wrap">
          <ChargePointModeButtons :charge-point-id="props.chargePointId" />
        </div>

        <!-- ///////////////// Instant charge settings /////////////////// -->
        <div v-if="chargeMode.value === 'instant_charging'">
          <ChargePointSofortSettings :charge-point-id="props.chargePointId" />
        </div>

        <!-- ///////////////// PV charge settings /////////////////// -->
        <div v-if="chargeMode.value === 'pv_charging'">
          <ChargePointPVSettings :charge-point-id="props.chargePointId" />
        </div>
        <!-- /////////////////  scheduled charging settings /////////////////// -->

        <div v-if="chargeMode.value === 'scheduled_charging'">
          <div class="row justify-between items-center">
            <div class="text-subtitle2 q-mr-sm q-mt-md">Termine:</div>
            <q-btn
              icon="add"
              color="positive"
              round
              size="sm"
              class="q-mt-md"
              @click="
                mqttStore.vehicleAddScheduledChargingPlan(props.chargePointId)
              "
            />
          </div>
          <q-expansion-item
            v-for="(plan, index) in plans.value"
            :key="index"
            expand-icon-toggle
            :default-opened="false"
            class="q-mt-md bg-primary rounded-borders-md"
            :class="plan.active ? 'active-border' : 'inactive-border'"
            :header-class="'cursor-pointer'"
            dense
          >
            <template v-slot:header>
              <ChargePointScheduledHeader
                :charge-point-id="props.chargePointId"
                :plan="plan"
              />
            </template>
            <ChargePointScheduledSettings
              :charge-point-id="props.chargePointId"
              :plan="plan"
            />
          </q-expansion-item>
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
import ChargePointSofortSettings from './ChargePointSofortSettings.vue';
import ChargePointPVSettings from './ChargePointPVSettings.vue';
import ChargePointScheduledSettings from './ChargePointScheduledSettings.vue';
import ChargePointScheduledHeader from './ChargePointScheduledHeader.vue';
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

const plans = computed(() =>
  mqttStore.vehicleScheduledChargingPlans(props.chargePointId),
);
</script>

<style scoped>
.rounded-borders-md {
  border-radius: 10px;
}
.active-border {
  border: 2px solid var(--q-positive);
}
.inactive-border {
  border: 2px solid var(--q-negative);
}

:deep(.q-expansion-item__container) .q-item {
  padding: 1px 3px; /* Reduce from default 8px 16px to 4px 8px */
}
</style>
