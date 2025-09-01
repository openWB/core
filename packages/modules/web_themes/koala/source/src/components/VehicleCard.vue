<template>
  <q-card
    ref="cardRef"
    class="card-width"
    :class="{ 'full-height': props.fullHeight }"
  >
    <q-card-section class="row">
      <div class="text-h6 text-bold ellipsis" :title="vehicle?.name">
        {{ vehicle?.name }}
      </div>
      <q-space />
      <q-btn
        v-if="props.closeButton"
        icon="close"
        flat
        round
        dense
        v-close-popup
      />
    </q-card-section>
    <q-separator class="q-mt-sm" />
    <q-card-section class="row q-mt-sm">
      <div class="col">
        <div class="text-subtitle2">Hersteller:</div>
        {{ vehicleInfo?.manufacturer || 'keine Angabe' }}
      </div>
      <div class="col q-pl-sm">
        <div class="text-subtitle2">Modell:</div>
        {{ vehicleInfo?.model || 'keine Angabe' }}
      </div>
    </q-card-section>
    <q-separator inset class="q-mt-sm" />
    <q-card-section>
      <VehicleConnectionStateIcon :vehicle-id="vehicleId" class="q-mt-sm" />
    </q-card-section>
    <div v-if="vehicleSocType">
      <q-separator inset class="q-mt-sm" />
      <q-card-section>
        <SliderDouble
          v-if="vehicleSocType"
          :current-value="vehicleSocValue"
          :readonly="true"
          :limit-mode="'none'"
          :vehicle-soc-type="vehicleSocType"
          :on-edit-soc="openSocDialog"
          :on-refresh-soc="refreshSoc"
        />
      </q-card-section>
    </div>
    <q-card-actions v-if="$slots['card-actions']" align="right">
      <slot name="card-actions"></slot>
    </q-card-actions>
    <!-- //////////////////////  modal soc dialog  //////////////////// -->
    <ManualSocDialog
      :vehicleId="props.vehicleId"
      v-model:socDialogVisible="socInputVisible"
    />
  </q-card>
</template>

<script setup lang="ts">
import { computed, ref } from 'vue';
import { useMqttStore } from 'src/stores/mqtt-store';
import { useQuasar } from 'quasar';
import SliderDouble from './SliderDouble.vue';
import ManualSocDialog from './ManualSocDialog.vue';
import VehicleConnectionStateIcon from './VehicleConnectionStateIcon.vue';

const cardRef = ref<{ $el: HTMLElement } | null>(null);

const props = defineProps<{
  vehicleId: number;
  closeButton?: boolean;
  fullHeight?: boolean;
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
</script>

<style lang="scss" scoped>
.card-width {
  width: 22em;
}

.q-card__section {
  padding-left: $space-base;
  padding-right: $space-base;
  padding-top: 0;
  padding-bottom: 0;
}

.q-card__section:first-of-type {
  padding-top: $space-base;
  padding-bottom: 0;
}

.q-card__section:last-of-type {
  padding-top: 0;
  padding-bottom: $space-base;
}

.q-card__section:not(:first-of-type):not(:last-of-type) {
  padding-top: 0;
  padding-bottom: 0;
}
</style>
