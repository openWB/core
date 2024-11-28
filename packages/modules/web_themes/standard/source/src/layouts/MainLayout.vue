<template>
  <q-layout view="lHh Lpr lFf" class="centered-container">
    <q-header elevated class="centered-container">
      <q-toolbar>
        <q-toolbar-title>openWB</q-toolbar-title>
        <q-btn dense flat round icon="menu">
          <q-menu anchor="bottom right" self="top right">
            <q-list dense>
              <q-item clickable v-close-popup>
                <q-item-section>Konfiguration</q-item-section>
              </q-item>

              <q-item clickable>
                <q-item-section>Darstellung</q-item-section>
                <q-menu anchor="top left" self="top right">
                  <q-list dense>
                    <q-item
                      v-for="theme in [
                        'light',
                        'dark',
                        'custom1',
                        'custom2',
                        'custom3',
                        'custom4',
                        'custom5',
                      ]"
                      :key="theme"
                      clickable
                      @click="setTheme(theme)"
                      :active="currentTheme === theme"
                      dense
                    >
                      <q-item-section>{{ theme }}</q-item-section>
                    </q-item>
                  </q-list>
                </q-menu>
              </q-item>
              <q-item clickable v-close-popup>
                <q-item-section>Hilfe</q-item-section>
              </q-item>
            </q-list>
          </q-menu>
        </q-btn>
      </q-toolbar>
    </q-header>
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
  position: relative;
}
.q-page-container {
  padding-top: 0 !important;
}
</style>
