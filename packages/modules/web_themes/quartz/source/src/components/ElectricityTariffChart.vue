<template>
  <div class="my-3">
    <div class="h-[220px]">
      <ChartjsLine
        v-if="points.length > 0"
        ref="chartRef"
        :data="chartData"
        :options="chartOptions"
        @click="onClick"
      />
      <p
        v-else
        class="mode-note"
      >
        Keine Preisdaten verfügbar.
      </p>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed, ref } from 'vue'
import { Line as ChartjsLine } from 'vue-chartjs'
import { Chart, type ChartOptions, type ChartData } from 'chart.js'
import annotationPlugin, { type AnnotationOptions } from 'chartjs-plugin-annotation'
import '@/utils/chartSetup'
import { useMqttStore } from '@/stores/mqtt-store'
import { getCssColor, hexToRgba } from '@/utils/color'
import { formatTooltipTime, eurPerWhToCtPerKwh } from '@/utils/format'

Chart.register(annotationPlugin)

/** The price threshold (ct/kWh) - clicking the chart emits the clicked hour's own price as the new threshold, same as koala's equivalent chart. */
const props = defineProps<{ modelValue?: number }>()
const emit = defineEmits<{ 'update:modelValue': [value: number] }>()

const mqttStore = useMqttStore()
const chartRef = ref<{ chart?: Chart } | null>(null)

// stepped, forward-filled one extra hour so the line reaches the end of the last real slot
// instead of stopping dead - same approach PriceDetailCard.vue's toStepSeries already uses
const points = computed(() => {
  const raw = Object.entries(mqttStore.electricityPrices)
    .map(([timestamp, price]) => ({ x: Number(timestamp) * 1000, y: eurPerWhToCtPerKwh(price) }))
    .sort((a, b) => a.x - b.x)
  if (raw.length === 0) return []
  const last = raw[raw.length - 1]
  const interval = raw.length > 1 ? last.x - raw[raw.length - 2].x : 60 * 60 * 1000
  return [...raw, { x: last.x + interval - 1000, y: last.y }]
})

// contiguous runs of "below/at threshold" (allowed - green) vs "above threshold" (blocked -
// red) price slots, shaded as background boxes - ported from koala's ElectricityTariffChart.vue,
// simplified to one pass over the series instead of two separate below/above loops
const priceAnnotations = computed<AnnotationOptions[]>(() => {
  if (props.modelValue === undefined || points.value.length === 0) return []
  const allowedColor = hexToRgba(getCssColor('--pv'), 0.2)
  const blockedColor = hexToRgba(getCssColor('--error'), 0.2)
  const series = points.value
  const annotations: AnnotationOptions[] = []
  let runStart = 0
  for (let i = 1; i <= series.length; i++) {
    const runAllowed = series[runStart].y <= props.modelValue
    if (i === series.length || series[i].y <= props.modelValue !== runAllowed) {
      annotations.push({
        type: 'box',
        drawTime: 'beforeDatasetsDraw',
        xMin: series[runStart].x,
        xMax: series[i - 1].x,
        borderWidth: 1,
        borderColor: runAllowed ? allowedColor : blockedColor,
        backgroundColor: runAllowed ? allowedColor : blockedColor,
      })
      runStart = i
    }
  }
  return annotations
})

const chartData = computed<ChartData<'line', { x: number; y: number }[]>>(() => ({
  datasets: [
    {
      label: 'Stromtarif',
      data: points.value,
      borderColor: getCssColor('--grid'),
      backgroundColor: 'transparent',
      stepped: true,
      pointRadius: 0,
      pointHoverRadius: 4,
      borderWidth: 2,
    },
  ],
}))

const chartOptions = computed<ChartOptions<'line'>>(() => {
  const mutedColor = getCssColor('--muted')
  const borderColor = getCssColor('--border')
  return {
    responsive: true,
    maintainAspectRatio: false,
    animation: false,
    interaction: { mode: 'index', intersect: false },
    plugins: {
      legend: { display: false },
      tooltip: {
        enabled: true,
        callbacks: {
          title: (items) => {
            const x = items[0]?.parsed.x
            return typeof x === 'number' ? formatTooltipTime(x) : ''
          },
          label: (item) => `${(item.parsed.y ?? 0).toLocaleString(undefined, { maximumFractionDigits: 2 })} ct/kWh`,
        },
      },
      annotation: { annotations: priceAnnotations.value },
    },
    scales: {
      x: {
        type: 'time',
        time: { unit: 'hour' },
        grid: { color: borderColor },
        ticks: { color: mutedColor, font: { size: 11 } },
      },
      y: {
        grid: { color: borderColor },
        ticks: { color: mutedColor, font: { size: 11 } },
        title: { display: true, text: 'Preis [ct/kWh]', color: mutedColor, font: { size: 12 } },
      },
    },
  }
})

function onClick(event: MouseEvent): void {
  const chart = chartRef.value?.chart
  if (!chart) return
  const elements = chart.getElementsAtEventForMode(event, 'index', { intersect: false }, true)
  if (elements.length === 0) return
  const point = points.value[elements[0].index]
  if (point) emit('update:modelValue', Math.round(point.y * 100) / 100)
}
</script>
