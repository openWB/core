<template>
  <div class="flex flex-col">
    <div
      class="flex flex-wrap items-center justify-center gap-x-3 gap-y-0.5"
      :class="position === 'above' ? 'order-1 mb-1.5' : 'order-2 mt-1.5'"
    >
      <span class="flex flex-none items-center gap-1.5 text-[11px] whitespace-nowrap text-muted sm:text-[13px]">
        <span class="legend-dot bg-car" />
        <b class="text-xs font-bold text-car sm:text-sm">{{ formatKw(total) }}</b>
        Gesamt
      </span>
      <span
        v-for="seg in segments"
        :key="seg.label"
        class="flex flex-none items-center gap-1.5 text-[11px] whitespace-nowrap text-muted sm:text-[13px]"
      >
        <span
          class="legend-dot"
          :style="segmentStyle(seg)"
        />
        <b
          class="font-bold"
          :style="{ color: `var(--${seg.colorVar})` }"
        >{{ formatKw(seg.value) }}</b>
        {{ seg.label }}
      </span>
    </div>
    <div
      class="flex h-[26px] overflow-hidden rounded-lg"
      :class="position === 'above' ? 'order-2' : 'order-1'"
    >
      <div
        v-for="seg in segments"
        :key="seg.label"
        :style="{ width: pct(seg.value) + '%', ...segmentStyle(seg) }"
      />
    </div>
  </div>
</template>

<script setup lang="ts">
import { formatKw } from '@/utils/format'
import type { FlowSegment } from '@/types/flow'

const props = defineProps<{
  segments: FlowSegment[]
  total: number
  /** Whether the total+legend line sits above or below the bar - the bar itself always stays on
   *  the side facing the arrow divider (sources: bar below; sinks: bar above). */
  position: 'above' | 'below'
}>()

function pct(value: number): number {
  return props.total > 0 ? (value / props.total) * 100 : 0
}

// a diagonal white-stripe overlay on top of the segment's own solid color - distinguishes
// segments that deliberately share one color (Zähler reuses --grid, same as Netz) without
// introducing a whole new color just for that one case
function segmentStyle(seg: FlowSegment): Record<string, string> {
  const color = `var(--${seg.colorVar})`
  if (!seg.hatched) return { background: color }
  return {
    backgroundColor: color,
    backgroundImage:
      'repeating-linear-gradient(45deg, rgba(255,255,255,0.45) 0, rgba(255,255,255,0.45) 2px, transparent 2px, transparent 5px)',
  }
}
</script>
