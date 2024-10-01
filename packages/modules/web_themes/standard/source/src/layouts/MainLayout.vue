<template>
  <q-layout view="lHh Lpr lFf" class="full-height">
    <!-- Header -->
    <q-header class="bg-grey-9 text-white">
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

<style scoped>
/* Make the layout take up the full viewport height */
.full-height {
  height: 100vh;
  display: flex;
  flex-direction: column;
}

.page-container {
  height: 100vh; /* Full viewport height minus the header height */
  display: flex;
  flex-direction: column;
}
</style>