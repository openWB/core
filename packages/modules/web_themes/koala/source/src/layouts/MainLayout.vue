<template>
  <q-layout view="lHh Lpr lFf" class="centered-container">
    <q-header elevated class="centered-container">
      <q-toolbar>
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
    <q-page-container class="column flex">
      <router-view />
    </q-page-container>
  </q-layout>
</template>

<script setup lang="ts">
import { computed, onMounted } from 'vue';
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
