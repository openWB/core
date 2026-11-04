<template>
  <div
    class="panel flex flex-1 items-center justify-center gap-1.5 overflow-hidden px-2 py-1.5 sm:gap-[7px] sm:px-[11px] sm:py-2"
    :class="[
      { 'cursor-pointer hover:border-accent': clickable },
      faultState === 1 ? 'chip-warning' : faultState !== undefined && faultState >= 2 ? 'chip-error' : '',
    ]"
    @click="clickable && $emit('click')"
  >
    <component
      :is="icon"
      class="shrink-0"
      :style="{ color: `var(--${color})` }"
    />
    <div class="min-w-0">
      <div class="truncate text-[10px] text-muted sm:text-[11px]">
        {{ label }}
      </div>
      <div class="truncate text-xs font-bold sm:text-sm">
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
  clickable?: boolean
  faultState?: number
}>()
defineEmits<{ click: [] }>()
</script>
