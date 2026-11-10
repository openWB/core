<template>
  <div class="px-1">
    <template v-if="sources.length > 0 || sinks.length > 0">
      <FlowBar
        :segments="sources"
        :total="sourceTotal"
        position="above"
      />

      <div class="my-1 flex items-center justify-center text-muted">
        <IconArrowDown
          :width="14"
          :height="14"
        />
      </div>

      <FlowBar
        :segments="sinks"
        :total="sinkTotal"
        position="below"
      />
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
import type { FlowSegment } from '@/types/flow'
import FlowBar from './FlowBar.vue'
import IconArrowDown from './icons/IconArrowDown.vue'

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
  if (counterSumPower.value < 0) {
    segments.push({ label: 'Zähler', value: -counterSumPower.value, colorVar: 'grid', hatched: true })
  }
  return segments.sort((a, b) => a.value - b.value)
})

const sinks = computed<FlowSegment[]>(() => {
  const segments: FlowSegment[] = []
  if (mqttStore.houseConsumption > 0) segments.push({ label: 'Haus', value: mqttStore.houseConsumption, colorVar: 'consumption' })
  if (mqttStore.chargePointSumPower > 0) segments.push({ label: 'Ladepunkte', value: mqttStore.chargePointSumPower, colorVar: 'chargepoint' })
  if (mqttStore.consumerPower > 0) segments.push({ label: 'Verbraucher', value: mqttStore.consumerPower, colorVar: 'consumer' })
  if (mqttStore.gridPower < 0) segments.push({ label: 'Netz-Einspeisung', value: -mqttStore.gridPower, colorVar: 'grid' })
  if (mqttStore.batteryPower > 0) segments.push({ label: 'Speicher', value: mqttStore.batteryPower, colorVar: 'battery' })
  if (counterSumPower.value > 0) {
    segments.push({ label: 'Zähler', value: counterSumPower.value, colorVar: 'grid', hatched: true })
  }
  return segments.sort((a, b) => a.value - b.value)
})

const sourceTotal = computed(() => sources.value.reduce((sum, s) => sum + s.value, 0))
const sinkTotal = computed(() => sinks.value.reduce((sum, s) => sum + s.value, 0))
</script>
