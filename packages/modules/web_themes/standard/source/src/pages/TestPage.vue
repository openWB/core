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
        :navigation="$q.screen.gt.xs"
        :arrows="$q.screen.gt.xs"
        class="full-height bg-transparent"
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
          <q-carousel-control position="bottom-right" :offset="[18, 18]">
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
    <q-tabs v-model="tab" dense align="justify">
      <q-tab name="lp">
        <q-icon name="ev_station" size="25px" color="primary" />
      </q-tab>
      <q-tab name="speicher">
        <q-icon name="battery_full" size="25px" color="warning" />
      </q-tab>
      <q-tab name="smartHome">
        <q-icon name="home" size="25px" color="accent" />
      </q-tab>
    </q-tabs>

    <!-- Tab Panels -->
    <q-tab-panels v-model="tab" animated class="col">
      <q-tab-panel name="lp" class="q-pa-none column">
        <ChargePointCarousel />
      </q-tab-panel>
      <q-tab-panel name="speicher" class="scroll">
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
      <q-tab-panel name="smartHome" class="scroll">
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
  </q-page>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue';
import { useQuasar } from 'quasar';
import DIA1 from '/src/assets/Dia_1.png';
import DIA2 from '/src/assets/Dia_2.png';
import ChargePointCarousel from 'src/components/ChargePointCarousel.vue';

// import { useMqttStore } from 'src/stores/mqtt-store';

defineOptions({
  name: 'IndexPage',
});

// const mqttStore = useMqttStore();

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

onMounted(() => {
  // mqttStore.subscribe(topicsToSubscribe);
});
</script>

<style scoped>
.scroll {
  overflow-y: auto;
}
</style>
