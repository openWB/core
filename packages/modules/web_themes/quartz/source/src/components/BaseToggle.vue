<template>
  <button
    type="button"
    class="relative inline-flex h-6 w-11 flex-none items-center rounded-full border-0 bg-[#d1d5db] p-0.5"
    role="switch"
    :aria-checked="modelValue"
    :class="{ 'bg-accent': modelValue }"
    @click="emit('update:modelValue', !modelValue)"
  >
    <span
      class="block h-5 w-5 rounded-full bg-white shadow-[0_1px_2px_rgba(0,0,0,0.3)] transition-transform duration-150 [transition-timing-function:ease]"
      :class="{ 'translate-x-5': modelValue }"
    />
  </button>
</template>

<script setup lang="ts">
defineProps<{ modelValue: boolean }>()
const emit = defineEmits<{ 'update:modelValue': [value: boolean] }>()
</script>
