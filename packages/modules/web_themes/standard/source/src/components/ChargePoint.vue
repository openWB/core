<template>
  <div class="q-ma-sm q-pa-sm"  v-if="chargePoint" style="max-width: 23em;" >
    <div class="row items-center text-h6" style="font-weight: bold">
      {{ chargePoint.name }}
      <q-icon
        :name="chargePoint.locked ? 'lock' : 'lock_open'"
        size="sm"
        :color="chargePoint.locked ? 'red' : 'green'"
        @click="toggleLock(chargePoint.id, chargePoint.locked)"
        style="cursor: pointer"
        class="q-ml-sm"
      />
      <q-icon
        :name="chargePoint.state ? 'power' : 'power_off'"
        size="sm"
        :color="chargePoint.state ? 'green' : 'red'"
      />
      <q-space />
      <q-icon name="settings" size="sm" />
    </div>
    <div
      class="row q-mt-md q-pa-sm bg-primary text-white"
      style="border-radius: 10px"
    >
      {{ chargePoint.message }}
    </div>
    <div style="margin-left: auto; margin-right: auto" display="block">
      <q-btn-group push rounded class="q-mt-md">
        <q-btn
          v-for="mode in chargeModes"
          :key="mode.value"
          :flat="selectedButton !== mode.value"
          :outline="selectedButton === mode.value"
          :glossy="selectedButton === mode.value"
          :label="mode.label"
          :color="mode.color"
          size="sm"
          @click="setChargeMode(mode.value)"
        />
      </q-btn-group>
    </div>
    <div class="row q-mt-sm">
      {{ chargePoint.power }}
    </div>
    <SliderQuasar class="q-mb-xl"></SliderQuasar>
  </div>
</template>

<script setup lang="ts">
import { computed, onMounted } from 'vue';
import SliderQuasar from './SliderQuasar.vue';
import { useMqttStore } from 'src/stores/mqtt-store';

const props = defineProps<{
  chargePointId: number;
}>();

const mqttStore = useMqttStore();

const topicsToSubscribe = <string[]>[
  'openWB/chargepoint/+/config',
  'openWB/chargepoint/+/set/manual_lock',
  'openWB/chargepoint/+/get/power',
  'openWB/chargepoint/+/get/state_str',
  'openWB/chargepoint/+/get/plug_state',
  'openWB/chargepoint/+/get/conected_vehicle',
  'openWB/chargepoint/+/get/connected_vehicle/config',
  'openWB/vehicle/template/charge_template/0',
];

const chargePoint = computed(() =>
  mqttStore.getChargePointDetails(props.chargePointId),
);
const selectedButton = computed(() => mqttStore.getChargeMode);

const chargeModes = [
  { value: 'sofort', label: 'Sofort', color: 'negative' },
  { value: 'pv', label: 'PV', color: 'positive' },
  { value: 'scheduled', label: 'Zeil', color: 'primary' },
  { value: 'standby', label: 'Standby', color: 'warning' },
  { value: 'stop', label: 'Stop', color: 'light' },
];

const toggleLock = (chargePointId: number, currentLockState: boolean) => {
  const topic = `openWB/chargepoint/${chargePointId}/set/manual_lock`;
  const newLockState = !currentLockState;
  mqttStore.updateTopic(topic, newLockState);
};

const setChargeMode = (mode: string) => {
  mqttStore.setChargeMode(mode);
};

onMounted(() => {
  mqttStore.subscribe(topicsToSubscribe);
});
</script>
