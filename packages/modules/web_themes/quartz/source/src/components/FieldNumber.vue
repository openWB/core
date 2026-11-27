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
      @input="onInput"
      @change="onChange"
    >
  </div>
</template>

<script setup lang="ts">
import { ref, watch } from 'vue'
import { parseNumberInput } from '@/utils/numberInput'

const props = defineProps<{
  label: string
  unit: string
  min?: number
  step?: number
  /** Rounds the displayed value (float noise from scaling). */
  decimals?: number
  modelValue: number
}>()
const emit = defineEmits<{ update: [value: number] }>()

function round(v: number): number {
  return props.decimals === undefined ? v : Number(v.toFixed(props.decimals))
}

const local = ref(round(props.modelValue))

watch(
  () => props.modelValue,
  (v) => {
    local.value = round(v)
  },
)

// an empty or half-typed field leaves the last good value alone instead of turning into 0
function onInput(event: Event): void {
  local.value = parseNumberInput((event.target as HTMLInputElement).value, local.value)
}

function onChange(event: Event): void {
  const value = round(parseNumberInput((event.target as HTMLInputElement).value, props.modelValue, props.min))
  local.value = value
  if (value !== round(props.modelValue)) emit('update', value)
}
</script>
