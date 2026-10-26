<template>
  <button
    type="button"
    :class="['rounded-full border px-[11px] py-[5px] text-xs', variantClasses[variant]]"
    @click="$emit('click')"
  >
    <slot />
  </button>
</template>

<script setup lang="ts">
withDefaults(defineProps<{ variant?: 'primary' | 'secondary' | 'danger' }>(), { variant: 'secondary' })
defineEmits<{ click: [] }>()

const variantClasses: Record<'primary' | 'secondary' | 'danger', string> = {
  primary: 'bg-accent border-accent text-white',
  secondary: 'bg-transparent border-border text-text',
  danger: 'bg-transparent border-grid text-grid',
}
</script>
