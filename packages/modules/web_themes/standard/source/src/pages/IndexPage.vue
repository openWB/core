<template>
  <q-page class="row items-center justify-evenly">
    <system-information title="System Information"></system-information>
  </q-page>
</template>

<style scoped></style>

<script setup lang="ts">
import SystemInformation from 'src/components/SystemInformation.vue';

defineOptions({
  name: 'TestPage',
});
</script>
