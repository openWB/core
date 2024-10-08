<template>
  <q-layout view="lHh Lpr lFf">
    <q-header elevated>
      <q-toolbar>
        <q-btn flat round icon="menu" aria-label="Menu" />
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

    <!-- Page container that takes the remaining height -->
    <q-page-container class="page-container">
      <router-view />
    </q-page-container>
  </q-layout>
</template>

<script setup lang="ts">
import { computed } from 'vue';
import { useQuasar } from 'quasar';
const $q = useQuasar();

defineOptions({
  name: 'MainLayout',
});

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
}
</script>

<style>
.page-container {
  height: 100vh;
  display: flex;
  flex-direction: column;
}
</style>
