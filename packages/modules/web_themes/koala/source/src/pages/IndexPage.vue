<template>
  <q-page
    class="column dashboard-page"
    :class="{ 'dashboard-active': showDesktopOverview }"
  >
    <!-- Top Carousel -->
    <div
      v-if="!showDesktopOverview || selectedCharts.length"
      class="row justify-center full-width chart-section"
      :class="{ 'desktop-chart-section': showDesktopOverview }"
    >
      <DesktopOverview v-if="showDesktopOverview" />
      <ChartCarousel v-else />
    </div>
    <q-dialog
      v-if="showDesktopOverview && remainingCharts.length"
      v-model="localDataStore.additionalChartsOpen"
      maximized
    >
      <q-card class="additional-charts column">
        <q-toolbar>
          <q-toolbar-title>Weitere Ansichten</q-toolbar-title>
          <q-btn
            v-close-popup
            flat
            round
            dense
            icon="close"
            aria-label="Weitere Ansichten schließen"
          />
        </q-toolbar>
        <div class="col additional-chart-content">
          <ChartCarousel
            include-dashboard
            :excluded-slides="localDataStore.desktopSlides"
          />
        </div>
      </q-card>
    </q-dialog>

    <!-- Navigation Tabs -->
    <div
      v-if="showDesktopOverview && !selectedDeviceSections.length"
      class="device-empty text-grey text-center q-pa-md"
      role="status"
    >
      Keine Gerätekategorie ausgewählt.
    </div>
    <DeviceDashboard
      v-else-if="showDesktopOverview && localDataStore.deviceLayout === 'grid'"
    />
    <div v-else-if="showDesktopOverview" class="device-overview">
      <section
        v-for="section in selectedDeviceSections"
        :key="section.name"
        :aria-label="section.label"
        :data-device-section="section.name"
        class="device-section"
      >
        <h2 class="text-subtitle1 text-weight-bold q-my-sm">
          <q-icon :name="section.icon" class="q-mr-sm" />{{ section.label }}
        </h2>
        <div class="device-section-content column">
          <component :is="deviceComponents[section.name]" />
        </div>
      </section>
    </div>
    <div v-else class="tab-section">
      <q-tabs v-model="tab" dense class="q-tabs__content--align-justify">
        <q-tab name="charge-points" title="Ladepunkte">
          <q-icon name="ev_station" size="md" />
        </q-tab>
        <q-tab name="vehicles" title="Fahrzeuge">
          <q-icon name="directions_car" size="md" />
        </q-tab>
        <q-tab v-if="accessBatteryAllowed" name="batteries" title="Speicher">
          <q-icon name="battery_full" size="md" />
        </q-tab>
        <q-tab v-if="consumersAvailable" name="consumers" title="Verbraucher">
          <q-icon name="power" size="md" color="primary" />
        </q-tab>
      </q-tabs>
      <!-- Tab Panels -->
      <q-tab-panels v-model="tab" class="col column">
        <!-- Charge Points -->
        <q-tab-panel name="charge-points" class="column">
          <ChargePointInformation />
        </q-tab-panel>
        <!-- Vehicles -->
        <q-tab-panel name="vehicles" class="column">
          <VehicleInformation />
        </q-tab-panel>
        <!-- Batteries -->
        <q-tab-panel
          v-if="accessBatteryAllowed"
          name="batteries"
          class="column"
        >
          <BatteryInformation />
        </q-tab-panel>
        <!-- Consumers -->
        <q-tab-panel v-if="consumersAvailable" name="consumers" class="column">
          <ConsumerInformation />
        </q-tab-panel>
      </q-tab-panels>
    </div>
  </q-page>
</template>

<script setup lang="ts">
import { computed, ref } from 'vue';
import { useMqttStore } from 'src/stores/mqtt-store';
import ChartCarousel from 'src/components/ChartCarousel.vue';
import DesktopOverview from 'src/components/DesktopOverview.vue';
import DeviceDashboard from 'src/components/DeviceDashboard.vue';
import { useLocalDataStore } from 'src/stores/localData-store';
import { useTopCharts } from 'src/components/charts/topCharts';
import { useDeviceSections } from 'src/components/deviceSections';
import ChargePointInformation from 'src/components/ChargePointInformation.vue';
import BatteryInformation from 'src/components/BatteryInformation.vue';
import VehicleInformation from 'src/components/VehicleInformation.vue';
import ConsumerInformation from 'src/components/ConsumerInformation.vue';

defineOptions({
  name: 'IndexPage',
});

const tab = ref<string>('charge-points');
const mqttStore = useMqttStore();
const localDataStore = useLocalDataStore();
const availableCharts = useTopCharts();
const availableDeviceSections = useDeviceSections();
const deviceComponents = {
  'charge-points': ChargePointInformation,
  vehicles: VehicleInformation,
  batteries: BatteryInformation,
  consumers: ConsumerInformation,
};
const selectedDeviceSections = computed(() =>
  availableDeviceSections.value.filter((section) =>
    localDataStore.dashboardDeviceSections.includes(section.name),
  ),
);
const showDesktopOverview = computed(() => localDataStore.desktopOverview);
const selectedCharts = computed(() =>
  availableCharts.value.filter((chart) =>
    localDataStore.desktopSlides.includes(chart.name),
  ),
);
const remainingCharts = computed(() =>
  availableCharts.value.filter(
    (chart) => !localDataStore.desktopSlides.includes(chart.name),
  ),
);

const accessBatteryAllowed = computed(() => {
  return mqttStore.batteryConfigured && mqttStore.batteryIds.length > 0;
});

const consumersAvailable = computed(() => {
  return mqttStore.consumerIds.length > 0;
});
</script>

<style scoped lang="scss">
.dashboard-page {
  width: 100%;
  min-width: 0;
}
.dashboard-active {
  --dashboard-gap: 12px;
  --dashboard-panel-padding: 8px;
  --dashboard-radius: 8px;
  gap: var(--dashboard-gap);
  padding: var(--dashboard-gap);
}
.chart-section {
  height: 40vh;
  min-height: 350px;
}

.desktop-chart-section {
  height: auto;
  min-height: 0;
}

.additional-chart-content {
  min-height: 0;
  position: relative;
}
.additional-charts {
  background: var(--q-background-2);
}

.device-overview {
  width: 100%;
  min-width: 0;
  display: flex;
  flex-direction: column;
  gap: var(--dashboard-gap);
}
.device-section,
.device-section-content {
  min-width: 0;
}
.device-section-content :deep(.carousel-height) {
  height: auto;
  width: 100%;
  max-width: 100%;
  min-width: 0;
}
.device-section-content :deep(.q-carousel),
.device-section-content :deep(.carousel-slide) {
  background: transparent;
  box-shadow: none;
}
.device-section-content :deep(.carousel-slide) {
  justify-content: flex-start;
  column-gap: var(--dashboard-gap);
  padding-left: 0;
  padding-right: 0;
}
.device-section-content :deep(.item-container) {
  flex: 0 0 auto;
  width: 22em;
  max-width: 100%;
  padding: 0;
}
.device-section-content :deep(.item-container > .q-card) {
  max-width: 100%;
}
.device-section-content :deep(.q-carousel__arrow) {
  top: auto;
  bottom: 8px;
}
.device-section-content :deep(.consumer-grid) {
  justify-content: start;
  grid-template-columns: repeat(auto-fill, minmax(min(100%, 22em), 22em));
  gap: var(--dashboard-gap);
  padding: 0;
}

.tab-section,
.tab-section :deep(.q-panel-parent .q-panel) {
  min-width: 0;
  flex-grow: 1;
  display: flex;
  flex-direction: column;
}

.tab-section .q-tab-panel {
  max-width: 100vw;
  flex-grow: 1;
}

@media screen and (max-width: $breakpoint-xs-max) {
  .dashboard-active {
    --dashboard-gap: 8px;
  }
  .tab-section .q-tab-panel {
    padding: 0;
  }
}
</style>
