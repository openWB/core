<template>
  <q-layout view="hHh lpr lFf">
    <q-header elevated>
      <q-toolbar>
        <q-btn dense flat round icon="menu" @click="drawer = !drawer" />
        <q-toolbar-title>openWB</q-toolbar-title>
        <q-btn
          flat
          round
          :icon="colorModeIcon"
          @click="toggleColorMode()"
          aria-label="Color-Mode"
        />
      </q-toolbar>
    </q-header>

    <q-drawer
      v-model="drawer"
      side="left"
      overlay
      elevated
      :breakpoint="500"
    >
      <!-- drawer content -->
      <q-scroll-area class="fit" :horizontal-thumb-style="{ opacity: '0' }">
        <q-list padding>

          <q-item
            clickable
            v-ripple
            href="/openWB/web/settings/#/Status"
          >
            <q-item-section avatar>
              <q-icon name="dashboard" />
            </q-item-section>

            <q-item-section>
              Status
            </q-item-section>
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

            <q-item-section>
              Ladeprotokoll
            </q-item-section>
          </q-item>

          <q-item
            clickable
            v-ripple
            href="/openWB/web/settings/#/Logging/Chart"
          >
            <q-item-section avatar>
              <q-icon name="area_chart" />
            </q-item-section>

            <q-item-section>
              Diagramme
            </q-item-section>
          </q-item>

          <q-separator />

          <q-item
            clickable
            v-ripple
            href="/openWB/web/settings/"
          >
            <q-item-section avatar>
              <q-icon name="settings" />
            </q-item-section>

            <q-item-section>
              Einstellungen
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
import { ref, computed, onMounted } from 'vue';
import { useQuasar } from 'quasar';
const $q = useQuasar();

defineOptions({
  name: 'MainLayout',
});

const drawer = ref(false);

/**
 * Computed property that returns the icon name for the color mode button.
 */
const colorModeIcon = computed(() => {
  return $q.dark.isActive ? 'dark_mode' : 'light_mode';
});

/**
 * Toggles the color mode of the application.
 */
function toggleColorMode() {
  $q.dark.toggle();
  localStorage.setItem('theme', $q.dark.isActive ? 'dark' : 'light');
}

onMounted(() => {
  const savedTheme = localStorage.getItem('theme') || 'light'; // Set light as default theme
  $q.dark.set(savedTheme === 'dark');
});
</script>

<style scoped>
.centered-container {
  max-width: 1000px;
  margin-left: auto;
  margin-right: auto;
}
</style>
