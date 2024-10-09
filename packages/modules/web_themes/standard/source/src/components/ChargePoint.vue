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
      class="column items-center justify-center"
    >
      <q-icon :name="item.icon" size="56px" />
      <div class="text-center q-mt-md">

        {{ item.text }}
      </div>
      <div>
        {{ item.message }}
      </div>
      <div>
        {{ item.locked }}
      </div>
      <div>
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
];

interface CarouselItem {
  name: string;
  icon: string;
  text: string;
  message: string;
  locked: boolean;
  power: number;
}

// Computed property for carousel items
const carouselItems = computed<CarouselItem[]>(() => {
  const chargePoints = mqttStore.getChargePointDetails;
  return chargePoints.map((cp) => ({
    name: cp.name,
    text: `Charge Point: ${cp.name}`,
    message: cp.message,
    locked: cp.locked,
    icon: 'ev_station',
    power: cp.power,
  }));
});

// Computed property to control carousel visibility
//const displayCarousel = computed(() => carouselItems.value.length > 0);

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
