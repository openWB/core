<template>
  <q-card ref="cardRef" class="full-height card-width">
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
      <SliderDouble
        v-if="vehicleSocType"
        class="q-mt-sm"
        :current-value="vehicleSocValue"
        :readonly="true"
        :limit-mode="'none'"
        :vehicle-soc-type="vehicleSocType"
        :on-edit-soc="openSocDialog"
        :on-refresh-soc="refreshSoc"
      />
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
import { computed, ref, onMounted } from 'vue';
import { useMqttStore } from 'src/stores/mqtt-store';
import { useQuasar } from 'quasar';
import SliderDouble from './SliderDouble.vue';
import ManualSocDialog from './ManualSocDialog.vue';
import VehicleConnectionStateIcon from './VehicleConnectionStateIcon.vue';

const cardRef = ref<{ $el: HTMLElement } | null>(null);
const emit = defineEmits<{
  (event: 'card-width', width: number | undefined): void;
}>();

const props = defineProps<{
  vehicleId: number;
}>();

const mqttStore = useMqttStore();
const $q = useQuasar();
const socInputVisible = ref<boolean>(false);
const openSocDialog = () => {
  socInputVisible.value = true;
};

const vehicle = computed(() => {
  return mqttStore.vehicleList.find((v) => v.id === props.vehicleId);
});

const vehicleInfo = computed(() => {
  return mqttStore.vehicleInfo(props.vehicleId);
});

const vehicleSocType = computed(() => {
  return mqttStore.vehicleSocType(props.vehicleId);
});

const vehicleSocValue = computed(() => {
  return mqttStore.vehicleSocValue(props.vehicleId) || 0;
});

const refreshSoc = () => {
  mqttStore.vehicleForceSocUpdate(props.vehicleId);
  $q.notify({
    type: 'positive',
    message: 'SoC Update angefordert.',
  });
};

onMounted(() => {
  const cardWidth = cardRef.value?.$el.offsetWidth;
  emit('card-width', cardWidth);
});
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
