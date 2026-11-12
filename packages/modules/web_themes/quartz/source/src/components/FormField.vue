<template>
  <label
    class="field-label"
    :class="{ 'mt-3': !first }"
    :for="id"
  >{{ label }}</label>
  <input
    :id="id"
    :value="modelValue"
    :type="type"
    class="field-select"
    :autocomplete="autocomplete"
    :disabled="disabled"
    v-bind="$attrs"
    @input="$emit('update:modelValue', ($event.target as HTMLInputElement).value)"
  >
</template>

<script setup lang="ts">
withDefaults(
  defineProps<{
    modelValue: string
    label: string
    id: string
    type?: string
    autocomplete?: string
    disabled?: boolean
    /** Omits the top margin otherwise applied to separate this field from the one above it. */
    first?: boolean
  }>(),
  { type: 'text', autocomplete: undefined, disabled: false, first: false },
)
defineEmits<{ 'update:modelValue': [value: string] }>()
</script>
