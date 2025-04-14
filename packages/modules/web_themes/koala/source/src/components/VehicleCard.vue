<template>
  <q-card class="full-height card-width">
    <q-card-section>
      <div class="row items-center text-h6 text-bold">
        <div class="col flex items-center">
          {{ vehicle?.name }}
        </div>
      </div>
      <div class="row q-mt-sm">
        <div class="col">
          <div class="text-subtitle2">Hersteller:</div>
          {{ vehicleInfo?.manufacturer || 'keine Angabe' }}
        </div>
        <div class="col q-pl-sm">
          <div class="text-subtitle2">Modell:</div>
          {{ vehicleInfo?.model || 'keine Angabe' }}
        </div>
      </div>
      <div class="row q-mt-sm">
        <div class="col">
          <div class="text-subtitle2">SoC Modul:</div>
          {{ vehicleSocModule || 'keine' }}
        </div>
      </div>
      <div v-if="vehicleSocValue !== null">
        <div class="slider-container">
          <q-slider
          :model-value="vehicleSocValue"
          color="green-7"
          class="current-slider q-mt-sm"
          track-size="1.5em"
          thumb-size="0px"
          :min="0"
          :max="100"
        />
        </div>
        <div class="row q-mt-sm">Ladestand: {{ vehicleSocValue }}%</div>
      </div>
    </q-card-section>
  </q-card>
</template>

<script setup lang="ts">
import { computed } from 'vue';
import { useMqttStore } from 'src/stores/mqtt-store';

const props = defineProps<{
  vehicleId: number | undefined;
}>();

const mqttStore = useMqttStore();

const vehicle = computed(() => {
  return mqttStore.vehicleList.find((v) => v.id === props.vehicleId);
});

const vehicleInfo = computed(() => {
  return mqttStore.vehicleInfo(props.vehicleId);
});

const vehicleSocModule = computed(() => {
  return mqttStore.vehicleSocModuleName(props.vehicleId);
});

const vehicleSocValue = computed(() => {
  return mqttStore.vehicleSocValue(props.vehicleId);
});
</script>

<style lang="scss" scoped>
.card-width {
  min-width: 24em;
}

.slider-container {
  position: relative;
  height: 40px;
}
</style>
