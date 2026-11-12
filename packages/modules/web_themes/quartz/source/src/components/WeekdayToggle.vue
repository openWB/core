<template>
  <div class="my-2.5 flex gap-1">
    <button
      v-for="(label, i) in dayLabels"
      :key="i"
      type="button"
      :class="[
        'flex-1 rounded-lg border py-1.5 text-[11px]',
        modelValue[i] ? 'border-text bg-text text-panel' : 'border-border bg-transparent text-text',
      ]"
      :aria-pressed="modelValue[i]"
      @click="toggle(i)"
    >
      {{ label }}
    </button>
  </div>
</template>

<script setup lang="ts">
const props = defineProps<{ modelValue: boolean[] }>()
const emit = defineEmits<{ update: [value: boolean[]] }>()

// Python's weekly[7] is Mon-Sun (datetime.weekday() order), matching these labels
const dayLabels = ['Mo', 'Di', 'Mi', 'Do', 'Fr', 'Sa', 'So']

function toggle(index: number): void {
  const next = [...props.modelValue]
  next[index] = !next[index]
  emit('update', next)
}
</script>
