<template>
  <div>
    <div class="text-muted">
      {{ label }}
    </div>
    <div class="font-bold">
      <slot>{{ value }}</slot>
    </div>
  </div>
</template>

<script setup lang="ts">
defineProps<{ label: string; value?: string }>()
</script>
