<template>
  <span
    v-if="label"
    class="field-label"
  >{{ label }}</span>
  <div class="seg-group">
    <button
      v-for="option in options"
      :key="option.value"
      type="button"
      class="seg-btn"
      :class="{ active: modelValue === option.value }"
      @click="$emit('update', option.value)"
    >
      {{ option.label }}
    </button>
  </div>
</template>

<script setup lang="ts" generic="T extends string | number">
defineProps<{
  label?: string
  modelValue: T | undefined
  options: readonly { value: T; label: string }[]
}>()
defineEmits<{ update: [value: T] }>()
</script>

<style scoped>
.seg-group {
  display: flex;
  gap: 6px;
  margin: 10px 0;
}

.seg-btn {
  flex: 1;
  font-size: 12px;
  padding: 6px 8px;
  border: 1px solid var(--border);
  border-radius: 8px;
  background: transparent;
  color: var(--text);
}

.seg-btn.active {
  background: var(--text);
  color: var(--panel);
  border-color: var(--text);
}
</style>
