<template>
  <span
    v-if="label"
    class="field-label"
  >{{ label }}</span>
  <div class="my-2.5 flex gap-1.5">
    <button
      v-for="option in options"
      :key="option.value"
      type="button"
      :disabled="option.disabled"
      :class="[
        'flex-1 rounded-lg border px-2 py-1.5 text-xs',
        option.disabled
          ? 'cursor-not-allowed border-border bg-transparent text-muted opacity-50'
          : modelValue === option.value
            ? 'border-text bg-text text-panel'
            : 'border-border bg-transparent text-text',
      ]"
      @click="!option.disabled && $emit('update', option.value)"
    >
      {{ option.label }}
    </button>
  </div>
</template>

<script setup lang="ts" generic="T extends string | number">
defineProps<{
  label?: string
  modelValue: T | undefined
  options: readonly { value: T; label: string; disabled?: boolean }[]
}>()
defineEmits<{ update: [value: T] }>()
</script>
