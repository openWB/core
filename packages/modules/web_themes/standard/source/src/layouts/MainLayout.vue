<template>
  <q-layout view="lHh Lpr lFf">
    <q-header elevated>
      <q-toolbar>
        <q-toolbar-title>openWB</q-toolbar-title>
        <q-btn flat round icon="menu" aria-label="Menu" />
      </q-toolbar>
    </q-header>

    <!-- Page container that takes the remaining height -->
    <q-page-container class="page-container">
      <router-view />
    </q-page-container>
  </q-layout>
</template>

<script setup lang="ts">
defineOptions({
  name: 'MainLayout',
});
</script>

<style>
.page-container {
  height: 100vh;
  display: flex;
  flex-direction: column;
}
</style>
