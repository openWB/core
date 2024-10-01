<template>
  <q-page class="bg-blue-grey-6 full-height flex column">
    <!-- Top Carousel -->
    <q-carousel
      v-model="slideTop"
      swipeable
      animated
      height="30vh"
      infinite
      class="bg-blue-grey-6 text-white rounded-borders custom-carousel"
    >
      <q-carousel-slide
        v-for="(item, index) in carouselItemsTop"
        :key="index"
        :name="item.name"
        class="column no-wrap flex-center"
      >
        <img
          :src="item.image"
          alt="Carousel Image"
          class="carousel-image"
          draggable="false"
        />
      </q-carousel-slide>
    </q-carousel>

    <!-- Card with Tabs for Details -->
    <q-card class="flex-grow-1 flex column overflow-hidden">
      <q-tabs v-model="tab" class="bg-grey-3 text-black">
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

      <q-separator />

      <q-tab-panels v-model="tab" animated class="flex-grow-1 flex column">
        <q-tab-panel name="lp" class="q-pa-none flex-grow-1 flex column">
          <q-carousel
            v-model="slideBottom"
            swipeable
            animated
            navigation
            infinite
            class="bg-blue-grey-6 text-white custom-carousel flex-grow-1"
            @mousedown.prevent
          >
            <q-carousel-slide
              v-for="(item, index) in carouselItems"
              :key="index"
              :name="item.name"
              class="column no-wrap flex-center"
            >
              <q-icon :name="item.icon" size="56px" />
              <div class="text-center q-mt-md">
                {{ item.text }}
              </div>
              <SliderQuasar class="q-mt-lg" />
            </q-carousel-slide>
          </q-carousel>
        </q-tab-panel>

        <q-tab-panel name="speicher" class="flex-grow-1 overflow-auto">
          <div class="q-pa-md">
            <p>Speicher</p>
            <div class="q-mt-md">
              <q-list bordered>
                <q-item>
                  <q-item-section>
                    <q-item-label>Leistung</q-item-label>
                    <q-item-label caption>22.0 kW</q-item-label>
                  </q-item-section>
                  <q-item-section>
                    <q-item-label>Geladen</q-item-label>
                    <q-item-label caption>7.2 kWh</q-item-label>
                  </q-item-section>
                </q-item>
                <q-item>
                  <q-item-section>
                    <q-item-label>Ladestand</q-item-label>
                    <q-item-label caption>30% (100 km)</q-item-label>
                  </q-item-section>
                  <q-item-section>
                    <q-item-label>Ladeziel</q-item-label>
                    <q-item-label caption>90% (360 km)</q-item-label>
                  </q-item-section>
                </q-item>
              </q-list>
            </div>
          </div>
        </q-tab-panel>

        <q-tab-panel name="smartHome" class="flex-grow-1 overflow-auto">
          <div class="q-pa-md">
            <p>Smart Home</p>
            <div class="q-mt-md">
              <q-list bordered>
                <q-item>
                  <q-item-section>
                    <q-item-label>Leistung</q-item-label>
                    <q-item-label caption>22.0 kW</q-item-label>
                  </q-item-section>
                  <q-item-section>
                    <q-item-label>Geladen</q-item-label>
                    <q-item-label caption>7.2 kWh</q-item-label>
                  </q-item-section>
                </q-item>
                <q-item>
                  <q-item-section>
                    <q-item-label>Ladestand</q-item-label>
                    <q-item-label caption>30% (100 km)</q-item-label>
                  </q-item-section>
                  <q-item-section>
                    <q-item-label>Ladeziel</q-item-label>
                    <q-item-label caption>90% (360 km)</q-item-label>
                  </q-item-section>
                </q-item>
              </q-list>
            </div>
          </div>
        </q-tab-panel>
      </q-tab-panels>
    </q-card>
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
//const slide = ref<number>(1);
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
.full-height {
  height: 100vh;
}

.custom-carousel {
  touch-action: pan-y;
}

.carousel-image {
  width: 100%;
  height: 100%;
  object-fit: contain;
  touch-action: none;
}

.q-page {
  padding: 0;
}

.q-card {
  border-radius: 0;
}
</style>
