<template>
  <svg
    class="base-icon"
    :style="color ? { color } : undefined"
    aria-hidden="true"
  >
    <use :href="`#icon-${iconName}`" />
  </svg>
</template>

<script setup lang="ts">
defineProps<{
  iconName: string;
  color?: string | null;
}>();
</script>

<style scoped>
.base-icon {
  width: 100%;
  height: 100%;
  fill: currentColor;
  vertical-align: middle;
  overflow: hidden;
}
</style>
