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
      <div class="row items-center text-h6" style="font-weight: bold">
        {{ item.text }}
        <q-icon
          :name="item.locked ? 'lock' : 'lock_open'"
          size="sm"
          :color="item.locked ? 'red' : 'green'"
          @click="toggleLock(item.id, item.locked)"
          style="cursor: pointer"
          class="q-ml-sm"
        />
        <q-icon
          :name="item.state ? 'power' : 'power_off'"
          size="sm"
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
            :flat="selectedButton !== 'sofort'"
            :outline="selectedButton === 'sofort'"
            :glossy="selectedButton === 'sofort'"
            label="Sofort"
            color="red"
            size="sm"
            @click="setChargeMode('sofort')"
          />
          <q-btn
            :flat="selectedButton !== 'pv'"
            :outline="selectedButton === 'pv'"
            :glossy="selectedButton === 'pv'"
            label="PV"
            color="green"
            size="sm"
            @click="setChargeMode('pv')"
          />
          <q-btn
            :flat="selectedButton !== 'scheduled'"
            :outline="selectedButton === 'scheduled'"
            :glossy="selectedButton === 'scheduled'"
            label="Zeil"
            color="blue"
            size="sm"
            @click="setChargeMode('scheduled')"
          />
          <q-btn
            :flat="selectedButton !== 'standby'"
            :outline="selectedButton === 'standby'"
            :glossy="selectedButton === 'standby'"
            label="Standby"
            color="grey"
            size="sm"
            @click="setChargeMode('standby')"
          />
          <q-btn
            :flat="selectedButton !== 'stop'"
            :outline="selectedButton === 'stop'"
            :glossy="selectedButton === 'stop'"
            label="Stop"
            color="black"
            size="sm"
            @click="setChargeMode('stop')"
          />
        </q-btn-group>
      </div>
      <div class="row q-mt-sm">
        {{ item.power }}
      </div>
      <SliderQuasar class="q-mb-xl"></SliderQuasar>
    </q-carousel-slide>
  </q-carousel>
</template>

<script setup lang="ts">
import { ref, computed, watch, onMounted } from 'vue';
import SliderQuasar from './SliderQuasar.vue';
import { useMqttStore } from 'src/stores/mqtt-store';

const mqttStore = useMqttStore();

const slide = ref<string | undefined>('');

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

const selectedButton = computed(() => mqttStore.getChargeMode);

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

const setChargeMode = (mode: string) => {
  mqttStore.setChargeMode(mode);
};

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
