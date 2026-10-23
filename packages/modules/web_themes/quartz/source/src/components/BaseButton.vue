<template>
  <button
    type="button"
    :class="['base-btn', variant]"
    @click="$emit('click')"
  >
    <slot />
  </button>
</template>

<script setup lang="ts">
withDefaults(defineProps<{ variant?: 'primary' | 'secondary' | 'danger' }>(), { variant: 'secondary' })
defineEmits<{ click: [] }>()
</script>

<style scoped>
.base-btn {
  font-size: 12px;
  padding: 5px 11px;
  border-radius: 999px;
  border: 1px solid var(--border);
}

.base-btn.primary {
  background: var(--accent);
  border-color: var(--accent);
  color: #fff;
}

.base-btn.secondary {
  background: transparent;
  color: var(--text);
}

.base-btn.danger {
  background: transparent;
  color: var(--grid);
  border-color: var(--grid);
}
</style>
