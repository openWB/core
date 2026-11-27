<template>
  <div
    class="panel flex flex-1 items-center justify-center gap-1.5 overflow-hidden px-2 py-1.5 sm:gap-[7px] sm:px-[11px] sm:py-2"
    :class="[
      { 'cursor-pointer hover:border-accent': clickable },
      faultState === 1 ? 'chip-warning' : faultState !== undefined && faultState >= 2 ? 'chip-error' : '',
    ]"
    :role="clickable ? 'button' : undefined"
    :tabindex="clickable ? 0 : undefined"
    @click="clickable && $emit('click')"
    @keydown.enter.prevent="clickable && $emit('click')"
    @keydown.space.prevent="clickable && $emit('click')"
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
      <div class="flex items-center gap-1 truncate text-xs font-bold sm:text-sm">
        <IconArrowDown
          v-if="direction"
          class="shrink-0 text-muted"
          :class="{ 'rotate-180': direction === 'out' }"
          :aria-label="directionLabel"
        />
        {{ value }}
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import type { Component } from 'vue'
import IconArrowDown from './icons/IconArrowDown.vue'

defineProps<{
  icon: Component
  label: string
  value: string
  color: string
  clickable?: boolean
  faultState?: number
  /** 'in' flows into the entity (Bezug, Laden), 'out' flows out (Einspeisung, Entladen); omitted when not meaningful. */
  direction?: 'in' | 'out'
  directionLabel?: string
}>()
defineEmits<{ click: [] }>()
</script>
