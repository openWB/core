<template>
  <div class="flex flex-wrap gap-2">
    <button
      v-for="option in options"
      :key="option.value"
      type="button"
      :class="[
        'rounded-full border',
        dense ? 'px-[9px] py-1 text-xs font-normal' : 'px-[14px] py-[7px] text-[13px] font-medium',
        modelValue === option.value ? 'border-accent bg-accent text-white' : 'border-border bg-transparent text-text',
      ]"
      @click="$emit('update', option.value)"
    >
      {{ option.label }}
    </button>
  </div>
</template>

<script setup lang="ts" generic="T extends string | number">
defineProps<{
  modelValue: T | undefined
  options: readonly { value: T; label: string }[]
  dense?: boolean
}>()
defineEmits<{ update: [value: T] }>()
</script>
