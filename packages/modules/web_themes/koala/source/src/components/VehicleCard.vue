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
      <VehicleConnectionStateIcon :vehicle-id="vehicleId" class="q-mt-sm" />
      <div v-if="vehicleSocValue !== null">
        <SliderDouble
          class="q-mt-sm"
          :current-value="vehicleSocValue"
          :readonly="true"
          :limit-mode="'none'"
        >
          <template #update-soc-icon>
            <q-icon
              v-if="vehicleSocModuleType === 'manual'"
              name="edit"
              size="xs"
              class="q-ml-xs cursor-pointer"
              @click="socInputVisible = true"
            >
              <q-tooltip>SoC eingeben</q-tooltip>
            </q-icon>
            <q-icon
              v-else-if="vehicleSocModuleType !== undefined"
              name="refresh"
              size="xs"
              class="q-ml-xs cursor-pointer"
              @click="refreshSoc"
            >
              <q-tooltip>SoC aktualisieren</q-tooltip>
            </q-icon>
          </template>
        </SliderDouble>
      </div>
      <slot name="card-footer"></slot>
    </q-card-section>
  </q-card>

  <!-- //////////////////////  input dialog Manual SoC   //////////////////// -->

  <ManualSocDialog
    :vehicleId="props.vehicleId"
    v-model:socDialogVisible="socInputVisible"
  />
</template>

<script setup lang="ts">
import { computed, ref } from 'vue';
import { useMqttStore } from 'src/stores/mqtt-store';
import { useQuasar } from 'quasar';
import SliderDouble from './SliderDouble.vue';
import ManualSocDialog from './ManualSocDialog.vue';
import VehicleConnectionStateIcon from './VehicleConnectionStateIcon.vue';

const props = defineProps<{
  vehicleId: number;
}>();

const mqttStore = useMqttStore();
const $q = useQuasar();
const socInputVisible = ref<boolean>(false);

const vehicle = computed(() => {
  return mqttStore.vehicleList.find((v) => v.id === props.vehicleId);
});

const vehicleInfo = computed(() => {
  return mqttStore.vehicleInfo(props.vehicleId);
});

const vehicleSocModuleType = computed(() => {
  return mqttStore.vehicleSocModule(props.vehicleId)?.type;
});

const vehicleSocValue = computed(() => {
  return mqttStore.vehicleSocValue(props.vehicleId);
});

const refreshSoc = () => {
  mqttStore.vehicleForceSocUpdate(props.vehicleId);
  $q.notify({
    type: 'positive',
    message: 'SoC Update angefordert.',
  });
};
</script>

<style lang="scss" scoped>
.card-width {
  width: 22em;
}

.slider-container {
  position: relative;
  height: 40px;
}
</style>
