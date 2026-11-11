<template>
  <label class="flex cursor-pointer items-center gap-2.5 text-[13px] text-muted">
    <BaseToggle
      :model-value="modelValue"
      @update:model-value="emit('update:modelValue', $event)"
    />
    {{ modelValue ? 'Dunkel' : 'Hell' }}
  </label>
</template>

<script setup lang="ts">
import BaseToggle from './BaseToggle.vue'

defineProps<{ modelValue: boolean }>()
const emit = defineEmits<{ 'update:modelValue': [value: boolean] }>()
</script>
