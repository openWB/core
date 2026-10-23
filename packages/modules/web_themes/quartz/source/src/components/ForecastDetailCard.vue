<template>
  <BaseModal
    :model-value="modelValue"
    title="Prognose"
    :width="880"
    @update:model-value="$emit('update:modelValue', $event)"
  >
    <div class="info-and-tabs">
      <div class="info-box">
        <div
          v-if="provider"
          class="info-row"
        >
          <span class="info-label">Anbieter</span>
          <span>{{ provider.name }}</span>
        </div>
        <div class="info-row">
          <span class="info-label">{{ energyLabel }}</span>
          <strong>{{ formatKwh(energySum) }}</strong>
        </div>
      </div>
      <BaseTabGroup
        :model-value="activeTab"
        :options="tabs"
        @update="activeTab = $event"
      />
    </div>

    <div style="min-height: 320px; margin: 16px 0">
      <ChartjsLine
        v-if="points.length > 0"
        :key="activeTab"
        :data="chartData"
        :options="chartOptions"
      />
      <p
        v-else
        class="mode-note"
      >
        Keine Prognosedaten verfügbar.
      </p>
    </div>

    <div
      v-if="statusMessage"
      class="status-box"
      :class="{ 'status-box-fault': hasFault }"
    >
      <strong>Modulmeldung</strong>
      <p>{{ statusMessage }}</p>
    </div>
  </BaseModal>
</template>

<script setup lang="ts">
import { computed, ref } from 'vue'
import { Line as ChartjsLine } from 'vue-chartjs'
import { type ChartOptions, type ChartData } from 'chart.js'
import '@/utils/chartSetup'
import { useMqttStore } from '@/stores/mqtt-store'
import { getCssColor, hexToRgba } from '@/utils/color'
import { formatKwh } from '@/utils/format'
import BaseModal from './BaseModal.vue'
import BaseTabGroup from './BaseTabGroup.vue'

defineProps<{ modelValue: boolean }>()
defineEmits<{ 'update:modelValue': [value: boolean] }>()

const mqttStore = useMqttStore()

const provider = computed(() => mqttStore.forecastProvider())
const hasFault = computed(() => mqttStore.forecastFaultState() > 0)
const statusMessage = computed(() => (mqttStore.forecastFaultState() > 0 ? mqttStore.forecastFaultMessage() : 'Kein Fehler.'))

const tabs = [
  { value: 'today', label: 'Heute' },
  { value: 'tomorrow', label: 'Morgen' },
  { value: 'all', label: 'Gesamt' },
] as const
const activeTab = ref<(typeof tabs)[number]['value']>('today')

function dayRange(offsetDays: number): { start: number; end: number } {
  const start = new Date()
  start.setDate(start.getDate() + offsetDays)
  start.setHours(0, 0, 0, 0)
  const end = new Date(start)
  end.setHours(23, 59, 59, 999)
  return { start: start.getTime(), end: end.getTime() }
}

const points = computed(() => {
  const all = mqttStore.forecastSeries
  if (activeTab.value === 'all') return all
  const { start, end } = dayRange(activeTab.value === 'today' ? 0 : 1)
  return all.filter((entry) => entry.timestamp >= start && entry.timestamp <= end)
})

const energyLabel = computed(() => {
  if (activeTab.value === 'all') return 'Gesamte Energie'
  return activeTab.value === 'today' ? 'Energie heute' : 'Energie morgen'
})

// left-Riemann sum over the series' own intervals - no fixed step assumed
const energySum = computed(() => {
  const series = points.value
  let total = 0
  for (let i = 0; i < series.length - 1; i++) {
    const hours = (series[i + 1].timestamp - series[i].timestamp) / 3_600_000
    total += series[i].power * hours
  }
  return total
})

const chartData = computed<ChartData<'line', { x: number; y: number }[]>>(() => {
  const color = getCssColor('--pv')
  return {
    datasets: [
      {
        label: 'Prognose',
        data: points.value.map((p) => ({ x: p.timestamp, y: p.power })),
        borderColor: color,
        backgroundColor: hexToRgba(color, 0.18),
        fill: true,
        pointRadius: 0,
        borderWidth: 2,
        tension: 0.2,
      },
    ],
  }
})

const chartOptions = computed<ChartOptions<'line'>>(() => {
  const mutedColor = getCssColor('--muted')
  const borderColor = getCssColor('--border')
  return {
    responsive: true,
    maintainAspectRatio: false,
    interaction: { mode: 'index', intersect: false },
    plugins: {
      legend: { display: false },
      tooltip: {
        enabled: true,
        callbacks: {
          title: (items) => {
            const x = items[0]?.parsed.x
            return typeof x === 'number'
              ? new Date(x).toLocaleString('de-DE', { day: '2-digit', month: '2-digit', hour: '2-digit', minute: '2-digit' })
              : ''
          },
          label: (item) => `${(item.parsed.y ?? 0).toLocaleString(undefined, { maximumFractionDigits: 2 })} kW`,
        },
      },
    },
    scales: {
      x: {
        type: 'time',
        time: { unit: activeTab.value === 'all' ? 'day' : 'hour' },
        grid: { color: borderColor },
        ticks: { color: mutedColor, font: { size: 11 } },
      },
      y: {
        suggestedMin: 0,
        grid: { color: borderColor },
        ticks: { color: mutedColor, font: { size: 12 } },
        title: { display: true, text: 'Leistung [kW]', color: mutedColor, font: { size: 12 } },
      },
    },
  }
})
</script>

<style scoped>
.info-and-tabs {
  display: flex;
  align-items: flex-start;
  gap: 16px;
}

.info-box {
  flex: 1;
}
</style>
