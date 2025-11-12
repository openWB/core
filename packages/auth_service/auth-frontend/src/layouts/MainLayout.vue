<template>
  <q-layout view="hHh lpr lFf">
    <q-header elevated>
      <q-toolbar>
        <q-btn flat dense round icon="menu" aria-label="Menu" @click="leftDrawerOpen = !leftDrawerOpen" />
        <q-toolbar-title> openWB </q-toolbar-title>
      </q-toolbar>
    </q-header>

    <q-drawer v-model="leftDrawerOpen" side="left" overlay elevated>
      <q-list>
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
    </q-drawer>

    <q-page-container>
      <router-view />
    </q-page-container>
  </q-layout>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue';
import { useQuasar } from 'quasar';

defineOptions({
  name: 'MainLayout',
});

const $q = useQuasar();
const leftDrawerOpen = ref(false);
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
