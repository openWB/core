<template>
  <q-dialog
    v-model="visible"
    :backdrop-filter="isSmallScreen ? '' : 'blur(4px)'"
  >
    <q-card class="card-width">
      <q-card-section>
        <div class="row nowrap q-mb-sm">
          <div class="text-h6">Begrenzung</div>
          <q-space />
          <q-btn icon="close" flat round dense v-close-popup />
        </div>
        <q-separator class="q-mt-sm q-mb-sm" />
        <div v-if="isSmallScreen" class="row q-pt-md full-width">
          <q-btn-dropdown
            class="col"
            transition-show="scale"
            transition-hide="scale"
            transition-duration="500"
            color="primary"
            :label="currentLimitModeLabel"
            size="md"
            dropdown-icon="none"
            cover
            push
          >
            <q-list>
              <template v-for="(mode, index) in limitModes" :key="mode.value">
                <q-item
                  clickable
                  v-close-popup
                  @click="limitMode.value = mode.value"
                  :active="limitMode.value === mode.value"
                  active-class="bg-primary text-white"
                >
                  <q-item-section class="text-center text-weight-bold">
                    <q-item-label>{{
                      mode.label.toLocaleUpperCase()
                    }}</q-item-label>
                  </q-item-section>
                </q-item>
                <q-separator v-if="index < limitModes.length - 1" />
              </template>
            </q-list>
          </q-btn-dropdown>
        </div>
        <div
          v-else
          class="row items-center justify-center q-ma-none q-pa-none no-wrap"
        >
          <q-btn-group class="col">
            <q-btn
              v-for="mode in limitModes"
              :key="mode.value"
              :color="limitMode.value === mode.value ? 'primary' : 'grey'"
              :label="mode.label"
              size="sm"
              class="col"
              @click="limitMode.value = mode.value"
            />
          </q-btn-group>
        </div>
        <SliderStandard
          v-if="limitMode.value === 'soc'"
          title="SoC-Limit für das Fahrzeug"
          :min="5"
          :max="100"
          :step="5"
          color="light-green-14"
          :track-size="'1em'"
          :limit-mode="limitMode.value"
          thumb-size="2.3em"
          thumb-color="light-green-14"
          unit="%"
          v-model="limitSoC.value"
          class="q-mt-md"
        />
        <SliderStandard
          v-if="limitMode.value === 'amount'"
          title="Energie-Limit"
          :min="1"
          :max="50"
          color="green-7"
          :track-size="'1em'"
          :limit-mode="limitMode.value"
          thumb-size="2.3em"
          thumb-color="green-7"
          unit="kWh"
          v-model="limitEnergy.value"
          class="q-mt-md"
        />
      </q-card-section>
    </q-card>
  </q-dialog>
</template>

<script setup lang="ts">
import { Screen, QDialog } from 'quasar';
import { useMqttStore } from 'src/stores/mqtt-store';
import SliderStandard from './SliderStandard.vue';
import { computed, ref, watch } from 'vue';

const props = defineProps<{
  chargePointId: number;
  modelValue: boolean;
}>();

const emit = defineEmits<{
  'update:model-value': [value: boolean];
}>();

const mqttStore = useMqttStore();

const isSmallScreen = computed(() => Screen.lt.sm);
const tempValue = ref<boolean>(props.modelValue);

const baseLimitModes = [
  { value: 'none', label: 'keine' },
  { value: 'soc', label: 'EV-SoC' },
  { value: 'amount', label: 'Energie' },
];

const limitModes = computed(() => {
  return baseLimitModes.filter((mode) => {
    // If vehicle has no SoC module - remove soc
    if (!vehicleSocType.value && mode.value === 'soc') {
      return false;
    }
    return true;
  });
});

const vehicleSocType = computed(() =>
  mqttStore.chargePointConnectedVehicleSocType(props.chargePointId),
)?.value;

const chargeMode = computed(
  () =>
    mqttStore.chargePointConnectedVehicleChargeMode(props.chargePointId)?.value,
);

const activeChargeLimitConfig = computed(() => {
  switch (chargeMode.value) {
    case 'instant_charging':
      return {
        mode: mqttStore.chargePointConnectedVehicleInstantChargeLimit(
          props.chargePointId,
        ),
        soc: mqttStore.chargePointConnectedVehicleInstantChargeLimitSoC(
          props.chargePointId,
        ),
        energy: mqttStore.chargePointConnectedVehicleInstantChargeLimitEnergy(
          props.chargePointId,
        ),
      };
    case 'pv_charging':
      return {
        mode: mqttStore.chargePointConnectedVehiclePvChargeLimit(
          props.chargePointId,
        ),
        soc: mqttStore.chargePointConnectedVehiclePvChargeLimitSoC(
          props.chargePointId,
        ),
        energy: mqttStore.chargePointConnectedVehiclePvChargeLimitEnergy(
          props.chargePointId,
        ),
      };
    case 'eco_charging':
      return {
        mode: mqttStore.chargePointConnectedVehicleEcoChargeLimit(
          props.chargePointId,
        ),
        soc: mqttStore.chargePointConnectedVehicleEcoChargeLimitSoC(
          props.chargePointId,
        ),
        energy: mqttStore.chargePointConnectedVehicleEcoChargeLimitEnergy(
          props.chargePointId,
        ),
      };
    default:
      return {
        mode: ref('none'),
        soc: ref(0),
        energy: ref(0),
      };
  }
});

const limitMode = computed(() => activeChargeLimitConfig.value.mode);
const limitSoC = computed(() => activeChargeLimitConfig.value.soc);
const limitEnergy = computed(() => activeChargeLimitConfig.value.energy);

const visible = computed({
  get: () => tempValue.value,
  set: (value) => {
    tempValue.value = value;
    emit('update:model-value', value);
  },
});

const currentLimitModeLabel = computed(
  () =>
    limitModes.value.find((mode) => mode.value === limitMode.value.value)
      ?.label,
);

watch(
  () => props.modelValue,
  (value) => {
    tempValue.value = value;
  },
);
</script>

<style scoped>
.card-width {
  width: 25em;
}
.q-btn-group .q-btn {
  min-width: 100px !important;
}

body.mobile .q-btn-group .q-btn {
  padding: 4px 8px;
  font-size: 12px !important;
  min-height: 30px;
}

:deep(.q-btn-dropdown__arrow-container) {
  width: 0;
  padding: 0;
  margin: 0;
}
</style>
