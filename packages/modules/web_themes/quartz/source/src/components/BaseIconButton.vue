<template>
  <button
    :class="[
      'flex items-center justify-center rounded-lg border border-border',
      size === 'sm' ? 'h-[22px] w-[22px] flex-none' : 'h-[26px] w-[26px]',
      active ? 'border-accent bg-accent text-white' : 'bg-transparent text-muted',
    ]"
    :aria-pressed="active"
    type="button"
    @click="$emit('click')"
  >
    <slot />
  </button>
</template>

<script setup lang="ts">
withDefaults(defineProps<{ active?: boolean; size?: 'sm' | 'md' }>(), { size: 'md' })
defineEmits<{ click: [] }>()
</script>
