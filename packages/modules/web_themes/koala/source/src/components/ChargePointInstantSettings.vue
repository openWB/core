<template>
  <SliderStandard
    v-if="acChargingEnabled"
    title="Stromstärke"
    :min="6"
    :max="32"
    unit="A"
    v-model="instantChargeCurrent.value"
    class="q-mt-sm"
  />
  <SliderStandard
    v-if="dcChargingEnabled"
    title="DC-Sollleistung"
    :min="4"
    :max="300"
    unit="kW"
    v-model="instantChargeCurrentDc.value"
    class="q-mt-sm"
  />

  <div v-if="acChargingEnabled">
    <div class="text-subtitle2 q-mt-sm q-mr-sm">Anzahl Phasen</div>
    <div class="row items-center justify-center q-ma-none q-pa-none no-wrap">
      <q-btn-group class="col">
        <q-btn
          v-for="option in phaseOptions"
          :key="option.value"
          :color="numPhases.value === option.value ? 'primary' : 'grey'"
          :label="option.label"
          size="sm"
          class="col"
          @click="numPhases.value = option.value"
        />
      </q-btn-group>
    </div>
  </div>
</template>

<script setup lang="ts">
import { useMqttStore } from 'src/stores/mqtt-store';
import SliderStandard from './SliderStandard.vue';
import { computed } from 'vue';

const props = defineProps<{
  chargePointId: number;
}>();

const mqttStore = useMqttStore();

const phaseOptions = [
  { value: 1, label: '1' },
  { value: 3, label: 'Maximum' },
];

const instantChargeCurrent = computed(() =>
  mqttStore.chargePointConnectedVehicleInstantChargeCurrent(
    props.chargePointId,
  ),
);

const dcChargingEnabled = computed(
  () => mqttStore.chargePointChargeType(props.chargePointId).value === 'DC',
);

const acChargingEnabled = computed(
  () => mqttStore.chargePointChargeType(props.chargePointId).value === 'AC',
);

const instantChargeCurrentDc = computed(() => {
  return mqttStore.chargePointConnectedVehicleInstantDcChargePower(
    props.chargePointId,
  );
});

const numPhases = computed(() =>
  mqttStore.chargePointConnectedVehicleInstantChargePhases(props.chargePointId),
);
</script>

<style scoped>
.q-btn-group .q-btn {
  min-width: 100px !important;
}

body.mobile .q-btn-group .q-btn {
  padding: 4px 8px;
  font-size: 12px !important;
  min-height: 30px;
}
</style>
