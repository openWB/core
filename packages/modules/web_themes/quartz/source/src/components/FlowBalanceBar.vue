<template>
  <div class="px-1 pt-1 pb-2">
    <template v-if="sources.length > 0 || sinks.length > 0">
      <div class="mb-1.5 text-center text-[13px] font-bold text-muted">
        {{ formatKw(sourceTotal) }}
      </div>
      <div class="flex h-[26px] overflow-hidden rounded-lg">
        <div
          v-for="seg in sources"
          :key="seg.label"
          :style="{ width: pct(seg.value, sourceTotal) + '%', background: `var(--${seg.colorVar})` }"
        />
      </div>
      <div class="mt-2 flex flex-wrap justify-center gap-x-3 gap-y-1">
        <span
          v-for="seg in sources"
          :key="seg.label"
          class="flex flex-none items-center gap-1.5 text-[11.5px] whitespace-nowrap text-muted"
        >
          <span
            class="legend-dot"
            :style="{ background: `var(--${seg.colorVar})` }"
          />
          <b
            class="font-bold"
            :style="{ color: `var(--${seg.colorVar})` }"
          >{{ formatKw(seg.value) }}</b>
          {{ seg.label }}
        </span>
      </div>

      <div class="my-2.5 flex items-center justify-center text-muted">
        <IconArrowDown
          :width="18"
          :height="18"
        />
      </div>

      <div class="mb-2 flex flex-wrap justify-center gap-x-3 gap-y-1">
        <span
          v-for="seg in sinks"
          :key="seg.label"
          class="flex flex-none items-center gap-1.5 text-[11.5px] whitespace-nowrap text-muted"
        >
          <span
            class="legend-dot"
            :style="{ background: `var(--${seg.colorVar})` }"
          />
          <b
            class="font-bold"
            :style="{ color: `var(--${seg.colorVar})` }"
          >{{ formatKw(seg.value) }}</b>
          {{ seg.label }}
        </span>
      </div>
      <div class="flex h-[26px] overflow-hidden rounded-lg">
        <div
          v-for="seg in sinks"
          :key="seg.label"
          :style="{ width: pct(seg.value, sinkTotal) + '%', background: `var(--${seg.colorVar})` }"
        />
      </div>
      <div class="mt-1.5 text-center text-[13px] font-bold text-muted">
        {{ formatKw(sinkTotal) }}
      </div>
    </template>
    <p
      v-else
      class="py-10 text-center text-sm text-muted"
    >
      Aktuell kein Energiefluss.
    </p>
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import { useMqttStore } from '@/stores/mqtt-store'
import { useCounters } from '@/composables/useCounters'
import { formatKw } from '@/utils/format'
import IconArrowDown from './icons/IconArrowDown.vue'

interface FlowSegment {
  label: string
  value: number
  colorVar: string
}

const mqttStore = useMqttStore()
const { counterIds } = useCounters()

// non-grid sub-meters (a wallbox circuit, a heat pump, etc.) that are NOT already folded into
// "Haus" server-side (is_home_consumption_counter resolves to false) - a counter that IS folded
// in must stay out of this sum, or its power would be counted both inside Haus and again here;
// reusing the --grid color matches the project's own "all counters are red" convention.
const counterSumPower = computed(() =>
  counterIds.value
    .filter((id) => !mqttStore.counterInstanceIsHomeConsumption(id))
    .reduce((sum, id) => sum + mqttStore.counterInstancePower(id), 0),
)

// live snapshot only (reuses whatever's already subscribed for the status chips) - a 100%-
// proportional pair of bars, not a time series, so there's nothing here for day/live mode or
// day navigation to apply to
const sources = computed<FlowSegment[]>(() => {
  const segments: FlowSegment[] = []
  if (mqttStore.pvPower > 0) segments.push({ label: 'PV', value: mqttStore.pvPower, colorVar: 'pv' })
  if (mqttStore.gridPower > 0) segments.push({ label: 'Netz-Bezug', value: mqttStore.gridPower, colorVar: 'grid' })
  if (mqttStore.batteryPower < 0) segments.push({ label: 'Speicher', value: -mqttStore.batteryPower, colorVar: 'battery' })
  if (mqttStore.chargePointSumPower < 0) {
    segments.push({ label: 'Ladepunkte (V2H)', value: -mqttStore.chargePointSumPower, colorVar: 'chargepoint' })
  }
  if (counterSumPower.value < 0) segments.push({ label: 'Zähler', value: -counterSumPower.value, colorVar: 'grid' })
  return segments
})

const sinks = computed<FlowSegment[]>(() => {
  const segments: FlowSegment[] = []
  if (mqttStore.houseConsumption > 0) segments.push({ label: 'Haus', value: mqttStore.houseConsumption, colorVar: 'consumption' })
  if (mqttStore.chargePointSumPower > 0) segments.push({ label: 'Ladepunkte', value: mqttStore.chargePointSumPower, colorVar: 'chargepoint' })
  if (mqttStore.consumerPower > 0) segments.push({ label: 'Verbraucher', value: mqttStore.consumerPower, colorVar: 'consumer' })
  if (mqttStore.gridPower < 0) segments.push({ label: 'Netz-Einspeisung', value: -mqttStore.gridPower, colorVar: 'grid' })
  if (mqttStore.batteryPower > 0) segments.push({ label: 'Speicher', value: mqttStore.batteryPower, colorVar: 'battery' })
  if (counterSumPower.value > 0) segments.push({ label: 'Zähler', value: counterSumPower.value, colorVar: 'grid' })
  return segments
})

const sourceTotal = computed(() => sources.value.reduce((sum, s) => sum + s.value, 0))
const sinkTotal = computed(() => sinks.value.reduce((sum, s) => sum + s.value, 0))

function pct(value: number, total: number): number {
  return total > 0 ? (value / total) * 100 : 0
}
</script>
