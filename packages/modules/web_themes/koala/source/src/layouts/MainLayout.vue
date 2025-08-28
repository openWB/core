<template>
  <q-layout view="hHh lpr lFf">
    <q-header elevated>
      <q-toolbar>
        <q-btn dense flat round icon="menu" @click="drawer = !drawer" />
        <q-toolbar-title>openWB</q-toolbar-title>
      </q-toolbar>
    </q-header>

    <q-drawer v-model="drawer" side="left" overlay elevated :breakpoint="500">
      <!-- drawer content -->
      <q-scroll-area class="fit" :horizontal-thumb-style="{ opacity: '0' }">
        <q-list padding>
          <q-item clickable v-ripple href="/openWB/web/settings/#/Status">
            <q-item-section avatar>
              <q-icon name="dashboard" />
            </q-item-section>

            <q-item-section> Status </q-item-section>
          </q-item>

          <q-separator />

          <q-item-label header>Auswertungen</q-item-label>

          <q-item
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

          <q-item clickable v-ripple href="/openWB/web/settings/">
            <q-item-section avatar>
              <q-icon name="settings" />
            </q-item-section>

            <q-item-section> Einstellungen </q-item-section>
          </q-item>

          <q-separator />

          <q-item-label header>Anzeigeeinstellungen</q-item-label>

          <q-item>
            <q-item-section avatar>
              <q-icon name="light_mode" />
            </q-item-section>

            <q-item-section>
              <q-item-label>Darstellungsmodus</q-item-label>
            </q-item-section>

            <q-item-section side>
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
            </q-item-section>
          </q-item>
        </q-list>
      </q-scroll-area>
    </q-drawer>

    <!-- Page container that takes the remaining height -->
    <q-page-container class="column flex centered-container">
      <router-view />
    </q-page-container>
  </q-layout>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue';
import { useQuasar } from 'quasar';
const $q = useQuasar();

defineOptions({
  name: 'MainLayout',
});

const drawer = ref(false);
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
.centered-container {
  max-width: $breakpoint-lg-min;
  margin-left: auto;
  margin-right: auto;
}
</style>
