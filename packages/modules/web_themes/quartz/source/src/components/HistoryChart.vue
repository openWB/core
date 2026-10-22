<template>
  <div
    class="panel"
    style="padding: 20px 24px 16px; margin-bottom: 24px"
  >
    <div style="display: flex; align-items: center; justify-content: space-between; flex-wrap: wrap; gap: 12px; margin-bottom: 12px">
      <h2 style="margin: 0; font-size: 16px; font-weight: 700">
        Verlauf &middot; Heute
      </h2>
      <div style="display: flex; align-items: center; gap: 16px; flex-wrap: wrap">
        <span
          v-for="item in legend"
          :key="item.label"
          class="legend-item"
        >
          <span
            class="legend-dot"
            :style="{ background: item.color }"
          />
          {{ item.label }}
        </span>
      </div>
    </div>

    <div style="min-height: 420px">
      <ChartjsLine
        v-if="hasData"
        :key="theme"
        :data="chartData"
        :options="chartOptions"
        :plugins="[nowLabelPlugin]"
      />
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import { Line as ChartjsLine } from 'vue-chartjs'
import {
  Chart,
  Tooltip,
  Legend,
  LineController,
  LineElement,
  PointElement,
  LinearScale,
  TimeScale,
  Filler,
  type ChartOptions,
  type ChartData,
  type Plugin,
} from 'chart.js'
import annotationPlugin from 'chartjs-plugin-annotation'
import 'chartjs-adapter-luxon'
import { useMqttStore } from '@/stores/mqtt-store'
import { useDailyLog } from '@/composables/useDailyLog'
import { getCssColor, hexToRgba } from '@/utils/color'

Chart.register(Tooltip, Legend, LineController, LineElement, PointElement, LinearScale, TimeScale, Filler, annotationPlugin)

// drawn manually instead of via chartjs-plugin-annotation's own label - that label kept
// getting clipped against the chart area regardless of position/yAdjust/clip settings
const nowLabelPlugin: Plugin<'line'> = {
  id: 'nowLabel',
  afterDraw(chart) {
    const x = chart.scales.x?.getPixelForValue(Date.now())
    if (x === undefined) return
    const { ctx, chartArea } = chart
    ctx.save()
    ctx.fillStyle = getCssColor('--muted')
    ctx.font = 'bold 11px sans-serif'
    ctx.textAlign = 'center'
    ctx.textBaseline = 'bottom'
    ctx.fillText('Jetzt', x, chartArea.top - 6)
    ctx.restore()
  },
}

const props = defineProps<{ theme: string }>()

const mqttStore = useMqttStore()
const { points } = useDailyLog()

const hasData = computed(() => points.value.length > 0)

// whole-day forecast, independent of how much real history exists - history can be
// flat/missing (component in error state, or just started) while the forecast for
// today is already known in full
const forecastToday = computed(() => {
  if (!mqttStore.forecastConfigured) return []
  const startOfToday = new Date().setHours(0, 0, 0, 0)
  const endOfToday = new Date().setHours(23, 59, 59, 999)
  return mqttStore.forecastSeries
    .filter((entry) => entry.timestamp >= startOfToday && entry.timestamp <= endOfToday)
    .map((entry) => ({ x: entry.timestamp, y: entry.power }))
})

interface SeriesDef {
  key: 'pv' | 'house' | 'grid' | 'battery' | 'consumer'
  label: string
  colorVar: string
  fill: boolean
}

const series: SeriesDef[] = [
  { key: 'pv', label: 'Erzeugung', colorVar: '--pv', fill: true },
  { key: 'house', label: 'Hausverbrauch', colorVar: '--consumption', fill: false },
  { key: 'grid', label: 'Netz', colorVar: '--grid', fill: false },
  { key: 'battery', label: 'Speicher', colorVar: '--battery', fill: false },
  { key: 'consumer', label: 'Verbraucher', colorVar: '--consumer', fill: false },
]

const legend = computed(() => {
  void props.theme
  const items = series.map((s) => ({ label: s.label, color: getCssColor(s.colorVar) }))
  if (mqttStore.forecastConfigured) {
    items.push({ label: 'Prognose', color: getCssColor('--pv') })
  }
  return items
})

const chartData = computed<ChartData<'line', { x: number; y: number }[]>>(() => {
  void props.theme
  const datasets: ChartData<'line', { x: number; y: number }[]>['datasets'] = series.map((s) => {
    const color = getCssColor(s.colorVar)
    return {
      label: s.label,
      data: points.value.map((p) => ({ x: p.timestamp, y: p[s.key] })),
      borderColor: color,
      backgroundColor: s.fill ? hexToRgba(color, 0.18) : 'transparent',
      fill: s.fill,
      borderWidth: s.fill ? 2.5 : 2,
      pointRadius: 0,
      tension: 0.2,
    }
  })
  if (forecastToday.value.length > 1) {
    const pvColor = getCssColor('--pv')
    datasets.push({
      label: 'Prognose',
      data: forecastToday.value,
      borderColor: pvColor,
      backgroundColor: 'transparent',
      fill: false,
      borderWidth: 2.5,
      pointRadius: 0,
      tension: 0.2,
      borderDash: [6, 6],
    })
  }
  return { datasets }
})

const chartOptions = computed<ChartOptions<'line'>>(() => {
  void props.theme
  const mutedColor = getCssColor('--muted')
  const borderColor = getCssColor('--border')
  return {
    responsive: true,
    maintainAspectRatio: false,
    layout: { padding: { top: 20 } },
    interaction: { mode: 'index', intersect: false },
    plugins: {
      legend: { display: false },
      tooltip: {
        enabled: true,
        callbacks: {
          title: (items) => {
            const x = items[0]?.parsed.x
            return typeof x === 'number'
              ? new Date(x).toLocaleTimeString('de-DE', { hour: '2-digit', minute: '2-digit' })
              : ''
          },
        },
      },
      annotation: {
        annotations: {
          now: {
            type: 'line',
            xMin: Date.now(),
            xMax: Date.now(),
            borderColor: mutedColor,
            borderWidth: 1.5,
            borderDash: [3, 4],
          },
        },
      },
    },
    scales: {
      x: {
        type: 'time',
        time: { unit: 'hour' },
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
.legend-item {
  display: flex;
  align-items: center;
  gap: 6px;
  font-size: 12px;
  color: var(--muted);
}

.legend-dot {
  width: 10px;
  height: 10px;
  border-radius: 3px;
  display: inline-block;
}
</style>
