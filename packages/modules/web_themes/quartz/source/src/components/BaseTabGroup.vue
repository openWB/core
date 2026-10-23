<template>
  <div
    class="tab-group"
    :class="{ dense }"
  >
    <button
      v-for="option in options"
      :key="option.value"
      type="button"
      :class="{ active: modelValue === option.value }"
      @click="$emit('update', option.value)"
    >
      {{ option.label }}
    </button>
  </div>
</template>

<script setup lang="ts" generic="T extends string | number">
defineProps<{
  modelValue: T | undefined
  options: readonly { value: T; label: string }[]
  dense?: boolean
}>()
defineEmits<{ update: [value: T] }>()
</script>

<style scoped>
.tab-group {
  display: flex;
  gap: 8px;
  flex-wrap: wrap;
}

.tab-group button {
  font-size: 13px;
  font-weight: 500;
  padding: 7px 14px;
  border: 1px solid var(--border);
  border-radius: 999px;
  background: transparent;
  color: var(--text);
}

.tab-group.dense button {
  font-size: 12px;
  padding: 4px 9px;
  font-weight: 400;
}

.tab-group button.active {
  background: var(--accent);
  border-color: var(--accent);
  color: #fff;
}
</style>
