<template>
  <q-layout view="lHh Lpr lFf" class="centered-container">
    <q-header elevated class="centered-container">
      <q-toolbar>
        <q-btn flat round icon="menu" aria-label="Menu" />
        <q-toolbar-title>openWB</q-toolbar-title>
        <q-btn-dropdown label="Display" dense unelevated no-caps>
          <q-list>
            <q-item
              v-for="theme in ['light', 'dark', 'custom']"
              :key="theme"
              clickable
              @click="setTheme(theme)"
              :active="currentTheme === theme"
              dense
            >
              <q-item-section>{{ theme }}</q-item-section>
            </q-item>
          </q-list>
        </q-btn-dropdown>
      </q-toolbar>
    </q-header>

    <!-- Page container that takes the remaining height -->
    <q-page-container class="column flex">
      <router-view />
    </q-page-container>
  </q-layout>
</template>

<script setup lang="ts">
import { useThemeManager } from 'src/composables/useThemeManager.ts';

defineOptions({
  name: 'MainLayout',
});

const { currentTheme, setTheme } = useThemeManager();
</script>

<style scoped>
.centered-container {
  max-width: 1000px;
  margin-left: auto;
  margin-right: auto;
}
</style>
