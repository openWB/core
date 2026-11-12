<template>
  <p
    v-if="faultState > 0 && faultMessage"
    class="mt-0 mb-2.5 text-xs text-grid"
  >
    {{ faultMessage }}
  </p>
</template>

<script setup lang="ts">
defineProps<{ faultState: number; faultMessage: string }>()
</script>
