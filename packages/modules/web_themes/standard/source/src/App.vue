<script setup>
import HelloWorld from './components/HelloWorld.vue'
</script>

<template>
  <main>
    <div class="wrapper">
      <HelloWorld />
    </div>
  </main>
</template>

<style scoped>
main {
  margin: 0;
  padding: 0;
  display: flex;
  align-items: center;
  justify-content: center;
}

.wrapper {
  padding-left: 2rem;
}
</style>
