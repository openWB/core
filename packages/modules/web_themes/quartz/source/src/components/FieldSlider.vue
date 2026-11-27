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

// shows the drag position, not the prop: Vue would reset the input to a stale value on any re-render mid-drag
const local = ref(props.modelValue)
const dragging = ref(false)

// follow external updates only while not dragging
watch(
  () => props.modelValue,
  (v) => {
    if (!dragging.value) local.value = v
  },
)

// discreteValues are mapped onto an index range so the thumb lands only on them
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
