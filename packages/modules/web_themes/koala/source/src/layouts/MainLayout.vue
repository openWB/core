<template>
  <q-layout view="hHh lpr lFf">
    <q-header elevated>
      <q-toolbar>
        <q-btn dense flat round icon="menu" @click="drawer = !drawer" />
        <q-toolbar-title>openWB</q-toolbar-title>
        <q-space />
        <connection-indicator />
        <user-indicator />
      </q-toolbar>
    </q-header>

    <q-drawer
      v-model="drawer"
      side="left"
      :width="Math.min(360, $q.screen.width - 24)"
      :overlay="!localDataStore.desktopOverview || $q.screen.width < 1024"
      elevated
      :breakpoint="drawerBreakpoint"
      :behavior="$q.screen.width <= drawerBreakpoint ? 'mobile' : 'desktop'"
    >
      <!-- drawer content -->
      <q-scroll-area
        class="fit"
        :content-style="{ width: '100%' }"
        :horizontal-thumb-style="{ opacity: '0' }"
      >
        <q-list class="navigation-list">
          <div v-if="accessStatusAllowed">
            <q-item clickable v-ripple href="/openWB/web/settings/#/Status">
              <q-item-section avatar>
                <q-icon name="dashboard" />
              </q-item-section>

              <q-item-section> Status </q-item-section>
            </q-item>

            <q-separator />
          </div>

          <div v-if="accessChargeLogAllowed || accessChartAllowed">
            <q-item-label header>Auswertungen</q-item-label>

            <q-item
              v-if="accessChargeLogAllowed"
              clickable
              v-ripple
              href="/openWB/web/settings/#/Logging/ChargeLog"
            >
              <q-item-section avatar>
                <q-icon name="table_chart" />
              </q-item-section>

              <q-item-section> Ladeprotokoll </q-item-section>
            </q-item>

            <q-item
              v-if="accessChartAllowed"
              clickable
              v-ripple
              href="/openWB/web/settings/#/Logging/Chart"
            >
              <q-item-section avatar>
                <q-icon name="area_chart" />
              </q-item-section>

              <q-item-section> Diagramme </q-item-section>
            </q-item>

            <q-separator />
          </div>

          <div v-if="accessSettingsAllowed">
            <q-item clickable v-ripple href="/openWB/web/settings/">
              <q-item-section avatar>
                <q-icon name="settings" />
              </q-item-section>

              <q-item-section> Einstellungen </q-item-section>
            </q-item>

            <q-separator />
          </div>

          <q-item-label header>Anzeigeeinstellungen</q-item-label>

          <q-item>
            <q-item-section avatar>
              <q-icon name="light_mode" />
            </q-item-section>

            <q-item-section>
              <div class="navigation-theme-controls">
                <q-item-label>Darstellungsmodus</q-item-label>
                <q-btn-group flat>
                  <q-btn
                    flat
                    round
                    :color="themeMode === 'light' ? 'primary' : ''"
                    icon="light_mode"
                    @click="setTheme('light')"
                    size="sm"
                    :disable="themeMode === 'light'"
                    aria-label="Light Mode"
                  >
                    <q-tooltip>Hell</q-tooltip>
                  </q-btn>
                  <q-btn
                    flat
                    round
                    :color="themeMode === 'dark' ? 'primary' : ''"
                    icon="dark_mode"
                    @click="setTheme('dark')"
                    size="sm"
                    :disable="themeMode === 'dark'"
                    aria-label="Dark Mode"
                  >
                    <q-tooltip>Dunkel</q-tooltip>
                  </q-btn>
                  <q-btn
                    flat
                    round
                    :color="themeMode === 'auto' ? 'primary' : ''"
                    icon="devices"
                    @click="setTheme('auto')"
                    size="sm"
                    :disable="themeMode === 'auto'"
                    aria-label="System Mode"
                  >
                    <q-tooltip>Systemeinstellung</q-tooltip>
                  </q-btn>
                </q-btn-group>
              </div>
            </q-item-section>
          </q-item>
          <q-separator />
          <q-item>
            <q-item-section>
              <q-toggle
                v-model="localDataStore.desktopOverview"
                label="Dashboard-Ansicht"
                dense
                class="navigation-toggle"
              />
            </q-item-section>
          </q-item>
          <div v-if="localDataStore.desktopOverview" class="navigation-options">
            <q-item-label caption class="navigation-caption"
              >Gemeinsam anzeigen</q-item-label
            >
            <div class="navigation-choices">
              <q-checkbox
                v-for="chart in navigationCharts"
                :key="chart.name"
                v-model="localDataStore.desktopSlides"
                :val="chart.name"
                :label="chart.label"
                class="full-width"
              />
            </div>
            <q-select
              v-if="hasHeightAdjustableChart"
              v-model="localDataStore.historyChartHeight"
              :options="historyChartHeights"
              emit-value
              map-options
              label="Höhe der Diagramme"
              dense
              outlined
              class="navigation-field"
            >
              <q-tooltip
                >Klein: 300 px, Mittel: 500 px, Groß: 800 px. Gesamthöhe der
                Diagrammkarten einschließlich Innenabständen und
                Bedienelementen.</q-tooltip
              >
            </q-select>
            <q-btn
              v-if="
                availableCharts.some(
                  (chart) => !localDataStore.desktopSlides.includes(chart.name),
                )
              "
              flat
              dense
              color="primary"
              icon="view_carousel"
              label="Weitere Ansichten"
              class="full-width"
              @click="openAdditionalCharts"
            />
            <div class="navigation-options">
              <q-select
                v-model="localDataStore.deviceLayout"
                :options="[
                  { label: 'Kachelraster', value: 'grid' },
                  { label: 'Bereiche untereinander', value: 'sections' },
                ]"
                emit-value
                map-options
                label="Anordnung"
                dense
                outlined
                class="navigation-field"
              />
              <div class="navigation-choices">
                <q-checkbox
                  v-for="section in availableDeviceSections"
                  :key="section.name"
                  v-model="localDataStore.dashboardDeviceSections"
                  :val="section.name"
                  :label="section.label"
                  class="full-width"
                />
              </div>
            </div>
          </div>
        </q-list>
      </q-scroll-area>
    </q-drawer>

    <!-- Page container that takes the remaining height -->
    <q-page-container class="column flex">
      <div
        class="centered-container"
        :class="{ 'dashboard-wide': localDataStore.desktopOverview }"
      >
        <router-view />
      </div>
    </q-page-container>
  </q-layout>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue';
import UserIndicator from 'src/components/UserIndicator.vue';
import ConnectionIndicator from 'src/components/ConnectionIndicator.vue';
import { useMqttStore } from 'src/stores/mqtt-store';
import {
  useLocalDataStore,
  historyChartHeights,
} from 'src/stores/localData-store';
import { useTopCharts } from 'src/components/charts/topCharts';
import { useDeviceSections } from 'src/components/deviceSections';
const mqttStore = useMqttStore();
const localDataStore = useLocalDataStore();
const availableCharts = useTopCharts();
const navigationCharts = computed(() =>
  [
    'daily_totals',
    'history_chart',
    'flow_diagram',
    'sankey_chart',
    'forecast_price_chart',
  ].flatMap((name) =>
    availableCharts.value.filter((chart) => chart.name === name),
  ),
);
const hasHeightAdjustableChart = computed(() =>
  availableCharts.value.some(
    (chart) =>
      chart.name !== 'daily_totals' &&
      localDataStore.desktopSlides.includes(chart.name),
  ),
);
const availableDeviceSections = useDeviceSections();

import { useQuasar } from 'quasar';
const $q = useQuasar();

defineOptions({
  name: 'MainLayout',
});

const accessSettingsAllowed = computed(() => mqttStore.accessSettingsAllowed);
const accessStatusAllowed = computed(() => mqttStore.accessStatusAllowed);
const accessChargeLogAllowed = computed(() => mqttStore.accessChargeLogAllowed);
const accessChartAllowed = computed(() => mqttStore.accessChartAllowed);

const drawer = ref(false);
const drawerBreakpoint = computed(() =>
  localDataStore.desktopOverview ? 1023 : 500,
);
const openAdditionalCharts = () => {
  drawer.value = false;
  localDataStore.additionalChartsOpen = true;
};
const themeMode = ref('auto');

const setTheme = (mode: 'light' | 'dark' | 'auto') => {
  themeMode.value = mode;
  if (mode === 'auto') {
    localStorage.removeItem('theme');
    $q.dark.set('auto');
  } else {
    $q.dark.set(mode === 'dark');
    localStorage.setItem('theme', mode);
  }
};

onMounted(() => {
  const savedTheme = localStorage.getItem('theme');
  if (savedTheme) {
    themeMode.value = savedTheme as 'light' | 'dark';
    $q.dark.set(savedTheme === 'dark');
  } else {
    themeMode.value = 'auto';
    $q.dark.set('auto');
  }
});
</script>

<style scoped lang="scss">
.navigation-list {
  width: 100%;
  padding: 16px;
}
.navigation-list :deep(.q-item) {
  min-height: 48px;
  padding: 8px 0;
}
.navigation-list :deep(.q-item__section--avatar) {
  min-width: 40px;
  padding-right: 0;
  align-items: center;
}
.navigation-list :deep(.q-item__label--header) {
  padding: 12px 0 8px;
}
.navigation-list :deep(.q-separator) {
  margin: 12px 0;
}
.navigation-theme-controls {
  display: flex;
  align-items: center;
  justify-content: space-between;
  flex-wrap: wrap;
  gap: 8px 12px;
}
.navigation-options {
  display: grid;
  gap: 12px;
  min-width: 0;
}
.navigation-caption {
  padding: 0;
}
.navigation-choices {
  display: grid;
}
.navigation-field,
.navigation-toggle {
  width: 100%;
  min-width: 0;
}
.navigation-toggle {
  min-height: 40px;
}
.navigation-toggle :deep(.q-toggle__inner) {
  margin-inline: 4px;
}
.navigation-list :deep(.q-checkbox__label),
.navigation-list :deep(.q-toggle__label) {
  padding-left: 0;
}
.centered-container {
  width: 100%;
  min-width: 0;
  max-width: $breakpoint-lg-min;
  margin-left: auto;
  margin-right: auto;
}
.dashboard-wide {
  max-width: none;
}
</style>
