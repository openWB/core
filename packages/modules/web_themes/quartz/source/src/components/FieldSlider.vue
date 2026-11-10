<template>
  <div class="my-3">
    <div class="mb-1.5 flex items-center justify-between text-[13px]">
      <span class="field-label m-0">{{ label }}</span>
      <span>{{ displayValue }}&nbsp;{{ displayUnit }}</span>
    </div>
    <input
      type="range"
      class="w-full accent-accent"
      :min="sliderMin"
      :max="sliderMax"
      :step="step ?? 1"
      :value="sliderPosition"
      :aria-label="`${label} in ${unit}`"
      @pointerdown="dragging = true"
      @pointerup="dragging = false"
      @input="local = toRealValue(Number(($event.target as HTMLInputElement).value))"
      @change="onChange"
    >
  </div>
</template>

<script setup lang="ts">
import { computed, ref, watch } from 'vue'

const props = defineProps<{
  label: string
  unit: string
  min: number
  max: number
  step?: number
  decimals?: number
  modelValue: number
  /** When set, the slider only lands on these values (e.g. [0, 6, 7, ..., 16]) - min/max are ignored. */
  discreteValues?: number[]
  /** A discreteValues entry (typically 0) to display as "Aus" instead of a number+unit. */
  offValue?: number
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

// a native <input type="range"> only knows a plain min/max/step range - discreteValues maps
// that onto an index space instead, so the thumb can only land on the configured values,
// e.g. "Aus" (0) + 6-16, never 1-5
const sliderMin = computed(() => (props.discreteValues ? 0 : props.min))
const sliderMax = computed(() => (props.discreteValues ? props.discreteValues.length - 1 : props.max))
const sliderPosition = computed(() => {
  if (!props.discreteValues) return local.value
  const index = props.discreteValues.indexOf(local.value)
  return index >= 0 ? index : 0
})
function toRealValue(sliderValue: number): number {
  return props.discreteValues ? props.discreteValues[sliderValue] ?? props.discreteValues[0] : sliderValue
}

const displayValue = computed(() => {
  if (props.offValue !== undefined && local.value === props.offValue) return 'Aus'
  return local.value.toLocaleString(undefined, {
    minimumFractionDigits: props.decimals ?? 0,
    maximumFractionDigits: props.decimals ?? 0,
  })
})
const displayUnit = computed(() => (props.offValue !== undefined && local.value === props.offValue ? '' : props.unit))

function onChange(event: Event): void {
  dragging.value = false
  const value = toRealValue(Number((event.target as HTMLInputElement).value))
  local.value = value
  emit('update', value)
}
</script>
