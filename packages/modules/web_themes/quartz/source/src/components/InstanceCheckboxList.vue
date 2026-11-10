<template>
  <label
    v-for="(item, idx) in items"
    :key="item.id"
    class="flex cursor-pointer items-center gap-[7px] text-xs text-muted"
  >
    <input
      type="checkbox"
      :checked="isVisible(item.id)"
      @change="setVisible(item.id, ($event.target as HTMLInputElement).checked)"
    >
    <span
      class="legend-dot"
      :style="{ background: instanceColor(color, idx) }"
    />
    {{ item.label }}
  </label>
</template>

<script setup lang="ts">
import { instanceColor } from '@/utils/color'

defineProps<{
  items: { id: string; label: string }[]
  color: string
  isVisible: (id: string) => boolean
  setVisible: (id: string, visible: boolean) => void
}>()
</script>
