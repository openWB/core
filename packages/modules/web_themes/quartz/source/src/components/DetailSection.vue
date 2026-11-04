<template>
  <div :class="['detail-section', tone === 'info' && 'detail-section-info']">
    <div class="settings-group-label mb-1.5">
      {{ title }}
    </div>
    <slot />
  </div>
</template>

<script setup lang="ts">
withDefaults(defineProps<{ title: string; tone?: 'neutral' | 'info' }>(), { tone: 'neutral' })
</script>
