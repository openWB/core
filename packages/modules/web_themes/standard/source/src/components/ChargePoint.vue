<template>
  <div class="q-ma-sm q-pa-sm" style="max-width: 23em">
    <div class="row items-center text-h6" style="font-weight: bold">
      {{ name }}
      <ChargePointLockIcon :charge-point-id="props.chargePointId" />
      <ChargePointStateIcon :charge-point-id="props.chargePointId" />
      <q-space />
      <q-icon name="settings" size="sm" />
    </div>
    <ChargePointFaultMessage :charge-point-id="props.chargePointId" />
    <ChargePointStateMessage :charge-point-id="props.chargePointId" />
    <div style="margin-left: auto; margin-right: auto" display="block">
      <ChargePointModeButtons :charge-point-id="props.chargePointId" />
    </div>
    <div class="row q-mt-sm">
      {{ power }}
    </div>
    <SliderQuasar class="q-mb-xl"></SliderQuasar>
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue';
import SliderQuasar from './SliderQuasar.vue';
import { useMqttStore } from 'src/stores/mqtt-store';
import ChargePointLockIcon from './ChargePointLockIcon.vue';
import ChargePointStateIcon from './ChargePointStateIcon.vue';
import ChargePointModeButtons from './ChargePointModeButtons.vue';
import ChargePointStateMessage from './ChargePointStateMessage.vue';
import ChargePointFaultMessage from './ChargePointFaultMessage.vue';

const props = defineProps<{
  chargePointId: number;
}>();

const mqttStore = useMqttStore();

const name = computed(() => mqttStore.chargePointName(props.chargePointId));
const power = computed(() =>
  mqttStore.chargePointPower(props.chargePointId, 'textValue'),
);
</script>
