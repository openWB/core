<template>
  <div class="weekday-group">
    <button
      v-for="(label, i) in dayLabels"
      :key="i"
      type="button"
      class="weekday-btn"
      :class="{ active: modelValue[i] }"
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

<style scoped>
.weekday-group {
  display: flex;
  gap: 4px;
  margin: 10px 0;
}

.weekday-btn {
  flex: 1;
  font-size: 11px;
  padding: 6px 0;
  border: 1px solid var(--border);
  border-radius: 8px;
  background: transparent;
  color: var(--text);
}

.weekday-btn.active {
  background: var(--text);
  color: var(--panel);
  border-color: var(--text);
}
</style>
