<template>
  <div v-for="(element, index) in options">
    <input
      class="form-check-input"
      type="checkbox"
      :value="element"
      v-model="v[index]"
      :id="'check' + index"
    />
    <label
      class="form-check-label px-2"
      :for="'check' + index"
      :style="optionColor(index)"
      >{{ options[index] }}</label
    >
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue'
const props = defineProps<{
  options: string[]
  modelValue: boolean[]
}>()
const emit = defineEmits(['update:modelValue'])
const v = computed({
  get() {
    return props.modelValue
  },
  set(value: boolean[]) {
    console.log ("SET CHECKBOX")
    emit('update:modelValue', value)
  },
})
function optionColor(index: number): {} {
  if (v.value[index]) {
    return { color: 'var(--color-pv)' }
  } else {
    return { color: 'var(--color-menu)' }
  }
}
</script>

<style scoped>
.form-check-input {
  background-color: var(--color-menu);
}
.form-check-input:checked {
  background-color: var(--color-pv);
}
</style>
