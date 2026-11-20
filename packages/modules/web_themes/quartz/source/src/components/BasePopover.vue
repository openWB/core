<template>
  <div class="relative">
    <slot
      name="trigger"
      :toggle="toggle"
    />
    <div
      v-if="modelValue"
      class="fixed inset-0 z-10"
      @click="emit('update:modelValue', false)"
    />
    <div
      v-if="modelValue"
      :class="['panel absolute z-[11] shadow-[0_8px_24px_rgba(0,0,0,0.12)]', panelClass]"
    >
      <slot />
    </div>
  </div>
</template>

<script setup lang="ts">
const props = defineProps<{ modelValue: boolean; panelClass?: string }>()
const emit = defineEmits<{ 'update:modelValue': [value: boolean] }>()

function toggle(): void {
  emit('update:modelValue', !props.modelValue)
}
</script>
