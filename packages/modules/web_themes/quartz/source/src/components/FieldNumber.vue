<template>
  <div class="my-3">
    <div class="mb-1.5 flex items-center justify-between text-[13px]">
      <span class="field-label m-0">{{ label }}</span>
      <span class="text-muted">{{ unit }}</span>
    </div>
    <input
      type="number"
      class="w-full rounded-[6px] border border-border bg-bg p-1.5 text-text"
      :min="min"
      :step="step ?? 1"
      :value="local"
      :aria-label="`${label} in ${unit}`"
      @input="local = Number(($event.target as HTMLInputElement).value)"
      @change="onChange"
    >
  </div>
</template>

<script setup lang="ts">
import { ref, watch } from 'vue'

const props = defineProps<{
  label: string
  unit: string
  min?: number
  step?: number
  modelValue: number
}>()
const emit = defineEmits<{ update: [value: number] }>()

const local = ref(props.modelValue)

watch(
  () => props.modelValue,
  (v) => {
    local.value = v
  },
)

function onChange(event: Event): void {
  const value = Number((event.target as HTMLInputElement).value)
  local.value = value
  emit('update', value)
}
</script>
