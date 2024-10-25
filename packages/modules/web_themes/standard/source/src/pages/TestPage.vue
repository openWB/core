<template>
  <q-page class="column">
    <!-- Top Carousel -->

    <div class="row justify-center">
      <q-carousel
        v-model="slideTop"
        v-model:fullscreen="fullscreen"
        swipeable
        control-color="primary"
        padding
        animated
        infinite
        :navigation="carouselItemsTop.length > 1"
        :arrows="carouselItemsTop.length > 1 && $q.screen.gt.xs"
        class="full-width bg-transparent"
      >
        <q-carousel-slide
          v-for="(item, index) in carouselItemsTop"
          :key="index"
          :name="item.name"
          class="col items-center justify-center"
        >
          <img
            :src="item.image"
            draggable="false"
            style="width: 100%; height: 100%; object-fit: contain"
          />
        </q-carousel-slide>

        <template v-slot:control>
          <q-carousel-control position="bottom-right">
            <q-btn
              push
              round
              dense
              text-color="primary"
              :icon="fullscreen ? 'fullscreen_exit' : 'fullscreen'"
              @click="fullscreen = !fullscreen"
            />
          </q-carousel-control>
        </template>
      </q-carousel>
    </div>

    <!-- Navigation Tabs -->
    <q-tabs v-model="tab" dense class="q-tabs__content--align-justify">
      <q-tab name="lp" title="Ladepunkte">
        <q-icon name="ev_station" size="md" color="primary" />
      </q-tab>
      <q-tab name="speicher" title="Speicher">
        <q-icon name="battery_full" size="md" color="warning" />
      </q-tab>
      <q-tab name="smartHome" title="SmartHome">
        <q-icon name="home" size="md" color="accent" />
      </q-tab>
    </q-tabs>

    <!-- Tab Panels -->
    <q-tab-panels v-model="tab" animated class="col">
      <q-tab-panel name="lp" class="q-pa-none column">
        <ChargePointCarousel />
      </q-tab-panel>
      <q-tab-panel name="speicher" class="scroll">
        <BatteryInformation />
      </q-tab-panel>
      <q-tab-panel name="smartHome" class="scroll">
        <SmartHomeInformation />
      </q-tab-panel>
    </q-tab-panels>
  </q-page>
</template>

<script setup lang="ts">
import { ref } from 'vue';
import { useQuasar } from 'quasar';
import DIA1 from '/src/assets/Dia_1.png';
import DIA2 from '/src/assets/Dia_2.png';
import ChargePointCarousel from 'src/components/ChargePointCarousel.vue';
import BatteryInformation from 'src/components/BatteryInformation.vue';
import SmartHomeInformation from 'src/components/SmartHomeInformation.vue';

defineOptions({
  name: 'IndexPage',
});

interface CarouselItemTop {
  name: string;
  image: string;
}

const $q = useQuasar();
const slideTop = ref<string>('DIA1');
const tab = ref<string>('lp');
const fullscreen = ref(false);
const carouselItemsTop: CarouselItemTop[] = [
  { name: 'DIA1', image: DIA1 },
  { name: 'DIA2', image: DIA2 },
];
</script>

<!-- <style scoped>
.scroll {
  overflow-y: auto;
}
</style> -->
