<template>
  <span class="d-flex flex-fill justify-content-between">
    <span class="minusButton" @click="stepDown">
      <i class="fa fa-xl fa-minus-square me-2"></i>
    </span>
    <input
      type="range"
      class="form-range flex-fill"
      :id="id"
      :min="min"
      :max="max"
      :step="step"
      v-model.number="v"
    />
    <span class="plusButton" @click="stepUp">
      <i class="fa fa-xl fa-plus-square ms-2"></i>
    </span>
  </span>
  <span class="d-flex justify-content-between align-items-start">
    <span class="minlabel ps-4"> {{ min }} </span>
    <span class="valuelabel">{{ v }} {{ unit }}</span>
    <span class="maxlabel pe-4"> {{ max }} </span>
  </span>
</template>

<script setup lang="ts">
import { computed } from 'vue'
const props = defineProps<{
  id: string
  min: number
  max: number
  step: number
  unit: string
  modelValue: number // for v-model binding
}>()
const emit = defineEmits(['update:modelValue'])
const v = computed({
  get() {
    return props.modelValue
  },
  set(value: number) {
    emit('update:modelValue', value)
  },
})
//methods
function stepDown() {
  if (v.value > props.min) {
    v.value = v.value - props.step
  }
}
function stepUp() {
  if (v.value < props.max) {
    v.value = v.value + props.step
  }
}
</script>

<style scoped>
.minlabel {
  color: var(--color-menu);
}
.maxlabel {
  color: var(--color-menu);
}
.valuelabel {
  color: var(--color-fg);
}
.minusButton {
  color: var(--color-menu);
}
.plusButton {
  color: var(--color-menu);
}
</style>
