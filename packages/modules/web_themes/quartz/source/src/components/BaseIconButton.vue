<template>
  <button
    :class="[
      'flex items-center justify-center rounded-full border border-border',
      size === 'sm' ? 'h-[22px] w-[22px] flex-none' : 'h-[26px] w-[26px]',
      tone ? `icon-btn-${tone}` : '',
      !tone && (active ? 'border-accent bg-accent text-white' : 'bg-transparent text-muted'),
    ]"
    :aria-pressed="active"
    type="button"
    @click="$emit('click')"
  >
    <slot />
  </button>
</template>

<script setup lang="ts">
withDefaults(defineProps<{ active?: boolean; size?: 'sm' | 'md'; tone?: 'ok' | 'warning' | 'error' }>(), { size: 'md', tone: undefined })
defineEmits<{ click: [] }>()
</script>

<style scoped>
.icon-btn-ok {
  color: var(--pv);
  border-color: color-mix(in srgb, var(--pv) 45%, transparent);
  background: color-mix(in srgb, var(--pv) 14%, transparent);
}

.icon-btn-warning {
  color: var(--warning);
  border-color: color-mix(in srgb, var(--warning) 45%, transparent);
  background: color-mix(in srgb, var(--warning) 14%, transparent);
}

.icon-btn-error {
  color: var(--error);
  border-color: color-mix(in srgb, var(--error) 45%, transparent);
  background: color-mix(in srgb, var(--error) 14%, transparent);
}
</style>
