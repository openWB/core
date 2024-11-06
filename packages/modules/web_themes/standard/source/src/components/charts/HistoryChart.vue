<template>
  <img
    :src="image"
    draggable="false"
    style="width: 100%; height: 100%; object-fit: contain"
  />
</template>

<script setup lang="ts">
defineOptions({
  name: 'HistoryChart',
});

const image = '/src/assets/Dia_2.png';
</script>
