<template>
  <div class="my-3">
    <div class="mb-1.5 flex items-center justify-between text-[13px]">
      <span class="field-label m-0">{{ label }}</span>
      <span>{{ displayValue }}&nbsp;{{ unit }}</span>
    </div>
    <input
      type="range"
      class="w-full accent-accent"
      :min="min"
      :max="max"
      :step="step ?? 1"
      :value="local"
      :aria-label="`${label} in ${unit}`"
      @pointerdown="dragging = true"
      @pointerup="dragging = false"
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
  min: number
  max: number
  step?: number
  decimals?: number
  modelValue: number
}>()
const emit = defineEmits<{ update: [value: number] }>()

// the rendered input always reflects 'local' (the live drag position), never the raw prop
// directly - Vue force-syncs an <input>'s value on every patch regardless of whether it
// changed, so binding straight to modelValue would yank the slider back to a stale value
// mid-drag the moment anything else in the app causes a re-render
const local = ref(props.modelValue)
const dragging = ref(false)

// only follow external updates (e.g. the backend echoing the saved value back) while the
// user isn't actively dragging
watch(
  () => props.modelValue,
  (v) => {
    if (!dragging.value) local.value = v
  },
)

const displayValue = ref('')
watch(
  local,
  (v) => {
    displayValue.value = v.toLocaleString(undefined, {
      minimumFractionDigits: props.decimals ?? 0,
      maximumFractionDigits: props.decimals ?? 0,
    })
  },
  { immediate: true },
)

function onChange(event: Event): void {
  dragging.value = false
  const value = Number((event.target as HTMLInputElement).value)
  local.value = value
  emit('update', value)
}
</script>
