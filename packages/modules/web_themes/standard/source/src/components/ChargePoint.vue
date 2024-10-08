<template>
  <q-carousel
    v-model="slideBottom"
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
        {{ chargePointNames }}
        {{ item.text }}
      </div>
      <SliderQuasar />
    </q-carousel-slide>
  </q-carousel>
</template>

<script setup lang="ts">
import { ref, onMounted, computed } from 'vue';
import SliderQuasar from './SliderQuasar.vue';
import { useMqttStore } from 'src/stores/mqtt-store';

const mqttStore = useMqttStore();
const topicsToSubscribe = <string[]>['openWB/chargepoint/+/config'];

const slideBottom = ref<string>('style');

interface CarouselItem {
  name: string;
  icon: string;
  text: string;
}

const carouselItems: CarouselItem[] = [
  {
    name: 'style',
    icon: 'style',
    text: 'Lorem ipsum dolor sit amet, consectetur adipiscing elit.',
  },
  {
    name: 'tv',
    icon: 'live_tv',
    text: 'Praesent bibendum, neque at hendrerit pretium, nunc nisi tempus nunc.',
  },
  {
    name: 'layers',
    icon: 'layers',
    text: 'Donec euismod, nisl eget ultricies ultricies, nunc nunc ultricies nunc.',
  },
  {
    name: 'map',
    icon: 'terrain',
    text: 'Sed do eiusmod tempor incididunt ut labore et dolore magna aliqua.',
  },
];

const chargePointNames = computed(() => mqttStore.getChargePointNames);

onMounted(() => {
  mqttStore.subscribe(topicsToSubscribe);
});
</script>
