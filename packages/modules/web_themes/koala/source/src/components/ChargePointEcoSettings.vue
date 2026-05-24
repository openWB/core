<template>
  <SliderStandard
    v-if="acChargingEnabled"
    title="Minimaler Dauerstrom unter der Preisgrenze"
    :min="6"
    :max="16"
    :step="1"
    unit="A"
    v-model="current"
    class="q-mt-md"
  />

  <SliderStandard
    v-if="dcChargingEnabled"
    title="Minimaler Dauerleistung unter der Preisgrenze"
    :min="4"
    :max="300"
    :step="1"
    unit="kW"
    v-model="dcPower.value"
    class="q-mt-md"
  />

  <div v-if="acChargingEnabled">
    <div class="text-subtitle2 q-mt-sm q-mr-sm">
      Anzahl Phasen bei Überschuss
    </div>
    <div class="row items-center justify-center q-ma-none q-pa-none no-wrap">
      <q-btn-group class="col">
        <q-btn
          v-for="option in phaseOptions"
          :key="option.value"
          :color="numPhases === option.value ? 'primary' : 'grey'"
          :label="option.label"
          size="sm"
          class="col"
          @click="numPhases = option.value"
        />
      </q-btn-group>
    </div>
  </div>
  <div v-if="etConfigured">
    <div class="text-subtitle2 q-my-sm">
      Preisgrenze für strompreisbasiertes Laden
    </div>
    <div class="row no-wrap items-center justify-between q-mb-xs q-gutter-x-xs">
      <div class="col-auto">
        <q-btn
          class="col-auto q-mr-xs disable-zoom"
          label="-1,00"
          color="grey"
          size="sm"
          dense
          @click="modifyMaxPrice(-1)"
        />
        <q-btn
          class="col-auto q-mr-xs disable-zoom"
          label="-0,10"
          color="grey"
          size="sm"
          dense
          @click="modifyMaxPrice(-0.1)"
        />
        <q-btn
          class="col-auto disable-zoom"
          label="-0,01"
          color="grey"
          size="sm"
          dense
          @click="modifyMaxPrice(-0.01)"
        />
      </div>
      <div class="col-auto q-mx-sm">
        {{
          maxPrice?.toLocaleString(undefined, {
            minimumFractionDigits: 2,
            maximumFractionDigits: 2,
          }) + ' ct/kWh'
        }}
      </div>
      <div class="col-auto">
        <q-btn
          class="col-auto q-mr-xs disable-zoom"
          label="+0,01"
          color="grey"
          size="sm"
          dense
          @click="modifyMaxPrice(0.01)"
        />
        <q-btn
          class="col-auto q-mr-xs disable-zoom"
          label="+0,10"
          color="grey"
          size="sm"
          dense
          @click="modifyMaxPrice(0.1)"
        />
        <q-btn
          class="col-auto disable-zoom"
          label="+1,00"
          color="grey"
          size="sm"
          dense
          @click="modifyMaxPrice(1)"
        />
      </div>
    </div>
    <q-field filled class="q-mt-sm">
      <ElectricityTariffChart
        :modelValue="maxPrice"
        @update:modelValue="maxPrice = $event"
      />
    </q-field>
  </div>
</template>

<script setup lang="ts">
import { useMqttStore } from 'src/stores/mqtt-store';
import SliderStandard from './SliderStandard.vue';
import ElectricityTariffChart from './ElectricityTariffChart.vue';
import { computed } from 'vue';

const props = defineProps<{
  chargePointId: number;
}>();

const mqttStore = useMqttStore();

const phaseOptions = [
  { value: 1, label: '1' },
  { value: 3, label: 'Maximum' },
  { value: 0, label: 'Automatik' },
];

const current = mqttStore.chargePointConnectedVehicleEcoChargeCurrent(
  props.chargePointId,
);

const dcChargingEnabled = computed(
  () => mqttStore.chargePointChargeType(props.chargePointId).value === 'DC',
);

const acChargingEnabled = computed(
  () => mqttStore.chargePointChargeType(props.chargePointId).value === 'AC',
);

const dcPower = computed(() =>
  mqttStore.chargePointConnectedVehicleEcoChargeDcPower(props.chargePointId),
);

const numPhases = mqttStore.chargePointConnectedVehicleEcoChargePhases(
  props.chargePointId,
);

const etConfigured = computed(() => mqttStore.etProviderConfigured);

const maxPrice = mqttStore.chargePointConnectedVehicleEcoChargeMaxPrice(
  props.chargePointId,
);

const modifyMaxPrice = (delta: number) => {
  maxPrice.value = (maxPrice.value || 0) + delta;
};
</script>

<style scoped>
.disable-zoom {
  touch-action: manipulation;
}
</style>
