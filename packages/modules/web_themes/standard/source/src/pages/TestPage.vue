<template>
  <q-page class="column">
    <!-- Top Carousel -->
    <div class="col-4">
      <q-carousel
        v-model="slideTop"
        swipeable
        animated
        infinite
        class="full-height bg-blue-grey-6"
      >
        <q-carousel-slide
          v-for="(item, index) in carouselItemsTop"
          :key="index"
          :name="item.name"
          class="column items-center justify-center"
        >
          <img :src="item.image" draggable="false" style="width: 100%; height: 100%; object-fit: contain" />
        </q-carousel-slide>
      </q-carousel>
    </div>

    <!-- Navigation Tabs -->
    <q-tabs v-model="tab" class="bg-blue-grey-4 text-black">
      <q-tab name="smartHome">
        <q-icon name="home" size="25px" color="grey-8" />
      </q-tab>
      <q-tab name="lp">
        <q-icon name="ev_station" size="25px" color="blue-7" />
      </q-tab>
      <q-tab name="speicher">
        <q-icon name="battery_full" size="25px" color="black" />
      </q-tab>
    </q-tabs>

    <!-- Tab Panels -->
    <q-tab-panels v-model="tab" animated class="col">
      <q-tab-panel name="lp" class="q-pa-none column">
        <q-carousel
          v-model="slideBottom"
          swipeable
          animated
          navigation
          infinite
          class="bg-blue-grey-6 text-white full-height"
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
            <SliderQuasar />
          </q-carousel-slide>
        </q-carousel>
      </q-tab-panel>
      <q-tab-panel name="speicher" class="scroll">
        <!-- Speicher content -->
      </q-tab-panel>
      <q-tab-panel name="smartHome" class="scroll">
        <!-- Smart Home content -->
      </q-tab-panel>
    </q-tab-panels>
  </q-page>
</template>

<script setup lang="ts">
import { ref } from 'vue';
import DIA1 from '/src/assets/Dia_1.png';
import DIA2 from '/src/assets/Dia_2.png';
import SliderQuasar from '../components/SliderQuasar.vue';

defineOptions({
  name: 'IndexPage',
});

// Type definitions for carousel items
interface CarouselItemTop {
  name: string;
  image: string;
}

interface CarouselItem {
  name: string;
  icon: string;
  text: string;
}

// States
const slideTop = ref<string>('DIA1');
const tab = ref<string>('lp');
const slideBottom = ref<string>('style');

// Data for carousels
const carouselItemsTop: CarouselItemTop[] = [
  { name: 'DIA1', image: DIA1 },
  { name: 'DIA2', image: DIA2 },
];

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
</script>

<style scoped>
.scroll {
  overflow-y: auto;
}
</style>