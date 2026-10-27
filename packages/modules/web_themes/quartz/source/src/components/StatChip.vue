<template>
  <div
    class="panel flex flex-1 items-center justify-center gap-[7px] whitespace-nowrap px-[11px] py-2"
    :class="[
      { 'cursor-pointer hover:border-accent': clickable },
      faultState === 1 ? 'chip-warning' : faultState !== undefined && faultState >= 2 ? 'chip-error' : '',
    ]"
    @click="clickable && $emit('click')"
  >
    <component
      :is="icon"
      :style="{ color: `var(--${color})` }"
    />
    <div>
      <div class="text-[11px] text-muted">
        {{ label }}
      </div>
      <div class="text-sm font-bold">
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
