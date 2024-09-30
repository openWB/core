<template>
  <q-layout view="lHh Lpr lFf">
    <q-header class="bg-grey-9 text-white">
      <q-toolbar>
        <q-toolbar-title>openWB</q-toolbar-title>
        <q-btn flat round icon="menu" aria-label="Menu" />
      </q-toolbar>
    </q-header>
    <q-page-container>
      <router-view />
    </q-page-container>
  </q-layout>
</template>

<script setup lang="ts">

defineOptions({
  name: 'MainLayout',
});
</script>
