<template>
  <div class="panel stat-chip">
    <component
      :is="icon"
      :style="{ color: `var(--${color})` }"
    />
    <div>
      <div class="stat-label">
        {{ label }}
      </div>
      <div class="stat-value">
        {{ value }}
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import type { Component } from 'vue'

defineProps<{
  icon: Component
  label: string
  value: string
  color: string
}>()
</script>

<style scoped>
.stat-chip {
  flex: 1 1 0;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 7px;
  padding: 8px 11px;
  white-space: nowrap;
}

.stat-label {
  font-size: 11px;
  color: var(--muted);
}

.stat-value {
  font-size: 14px;
  font-weight: 700;
}
</style>
