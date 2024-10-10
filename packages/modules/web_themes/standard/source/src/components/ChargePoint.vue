<template>
  <q-carousel
    v-model="slide"
    swipeable
    animated
    navigation
    arrows
    control-color="primary"
    infinite
    class="full-height"
    @mousedown.prevent
  >
    <q-carousel-slide
      v-for="(item, index) in carouselItems"
      :key="index"
      :name="item.name"
      class="column align-center"
    >
      <!-- <q-icon :name="item.icon" size="56px" /> -->
      <div class="row items-center text-h6" style="font-weight: bold">
        {{ item.text }}
        <q-icon
          :name="item.locked ? 'lock' : 'lock_open'"
          size="25px"
          :color="item.locked ? 'red' : 'green'"
          @click="toggleLock(item.id, item.locked)"
          style="cursor: pointer"
          class="q-ml-sm"
        />
        <q-icon
          :name="item.state ? 'power' : 'power_off'"
          size="25px"
          :color="item.state ? 'green' : 'red'"
        />
        <q-space />
        <q-icon name="settings" size="25px" />
      </div>
      <div
        class="row q-mt-md q-pa-sm bg-primary text-white"
        style="border-radius: 10px"
      >
        {{ item.message }}
      </div>
      <div style="margin-left: auto; margin-right: auto" display="block">
        <q-btn-group push rounded class="q-mt-md">
          <q-btn
            flat
            label="Sofort"
            color="red"
            size="sm"
            :model-value="selectedButton === 'Sofort'"
            @click="setChargeMode(item.id, 'instant_charging', 'chargemode')"
          />
          <q-btn
            flat
            label="PV"
            color="green"
            size="sm"
            :model-value="selectedButton === 'PV'"
            @click="setChargeMode(item.id, 'pv_charging', 'chargemode')"
          />
          <q-btn
            flat
            label="Zeil"
            color="blue"
            size="sm"
            :model-value="selectedButton === 'Zeil'"
            @click="setChargeMode(item.id, 'scheduled_charging', 'chargemode')"
          />
          <q-btn
            flat
            label="Standby"
            color="grey"
            size="sm"
            :model-value="selectedButton === 'Standby'"
            @click="setChargeMode(item.id, 'standby', 'chargemode')"
          />
          <q-btn
            flat
            label="Stop"
            color="black"
            size="sm"
            :model-value="selectedButton === 'Stop'"
            @click="setChargeMode(item.id, 'stop', 'chargemode')"
          />
        </q-btn-group>
      </div>
      <div class="row q-mt-sm">
        {{ item.power }}
      </div>
      <SliderQuasar />
    </q-carousel-slide>
  </q-carousel>
</template>

<script setup lang="ts">
import { ref, computed, watch, onMounted } from 'vue';

import SliderQuasar from './SliderQuasar.vue';
import { useMqttStore } from 'src/stores/mqtt-store';

const mqttStore = useMqttStore();

const slide = ref<string>('');
const topicsToSubscribe = <string[]>[
  'openWB/chargepoint/+/config',
  'openWB/chargepoint/+/set/manual_lock',
  'openWB/chargepoint/+/get/power',
  'openWB/chargepoint/+/get/state_str',
  'openWB/chargepoint/+/get/plug_state',
  'openWB/chargepoint/+/get/conected_vehicle',
  'openWB/chargepoint/+/get/connected_vehicle/config',
];

interface CarouselItem {
  id: string;
  name: string;
  icon: string;
  text: string;
  message: string;
  locked: boolean;
  state: boolean;
  power: number;
}

const selectedButton = ref<string>('Stop');
//const selectMode = ref<string>('chargemode');

// Computed property for carousel items
const carouselItems = computed<CarouselItem[]>(() => {
  const chargePoints = mqttStore.getChargePointDetails;
  return chargePoints.map((cp) => ({
    id: cp.id,
    name: cp.name,
    text: cp.name,
    message: cp.message,
    locked: cp.locked,
    state: cp.state,
    icon: 'ev_station',
    power: cp.power,
  }));
});

const toggleLock = (chargePointId: string, currentLockState: boolean) => {
  const topic = `openWB/chargepoint/${chargePointId}/set/manual_lock`;
  const newLockState = !currentLockState;
  mqttStore.updateTopic(topic, newLockState);
};

const setChargeMode = (
  chargePointId: string,
  mode: string,
  selectMode: string,
) => {
  const topic = `openWB/chargepoint/${chargePointId}/get/connected_vehicle/config`;
  mqttStore.updateTopic(topic, mode, selectMode);
  selectedButton.value = mode;
};

// Watch for changes in carouselItems and set initial slide when data becomes available
watch(
  carouselItems,
  (newItems) => {
    if (newItems.length > 0 && !slide.value) {
      slide.value = newItems[0].name;
    }
  },
  { immediate: true },
);

onMounted(() => {
  mqttStore.subscribe(topicsToSubscribe);
});
</script>

<style scoped></style>
