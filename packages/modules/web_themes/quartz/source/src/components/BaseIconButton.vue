<template>
  <button
    class="icon-btn"
    :class="{ active, sm: size === 'sm' }"
    :aria-pressed="active"
    type="button"
    @click="$emit('click')"
  >
    <slot />
  </button>
</template>

<script setup lang="ts">
withDefaults(defineProps<{ active?: boolean; size?: 'sm' | 'md' }>(), { size: 'md' })
defineEmits<{ click: [] }>()
</script>

<style scoped>
.icon-btn {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 26px;
  height: 26px;
  border: 1px solid var(--border);
  border-radius: 8px;
  background: transparent;
  color: var(--muted);
}

.icon-btn.sm {
  width: 22px;
  height: 22px;
  flex: none;
}

.icon-btn.active {
  background: var(--accent);
  border-color: var(--accent);
  color: #fff;
}
</style>
