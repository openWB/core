<template>
  <div class="my-3">
    <div :class="{ 'h-[220px]': points.length > 0 }">
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
import { cardChartOptions } from '@/utils/chartOptions'
import { useMqttStore } from '@/stores/mqtt-store'
import { getCssColor, hexToRgba } from '@/utils/color'
import { formatTooltipTime, eurPerWhToCtPerKwh } from '@/utils/format'
import { priceRuns } from '@/utils/priceRuns'

Chart.register(annotationPlugin)

/** The price threshold in ct/kWh; clicking the chart sets it to the clicked slot's price. */
const props = defineProps<{ modelValue?: number }>()
const emit = defineEmits<{ 'update:modelValue': [value: number] }>()

const mqttStore = useMqttStore()
const chartRef = ref<{ chart?: Chart } | null>(null)

// stepped, with one extra point so the line reaches the end of the last slot
const points = computed(() => {
  const raw = Object.entries(mqttStore.electricityPrices)
    .map(([timestamp, price]) => ({ x: Number(timestamp) * 1000, y: eurPerWhToCtPerKwh(price) }))
    .sort((a, b) => a.x - b.x)
  if (raw.length === 0) return []
  const last = raw[raw.length - 1]
  const interval = raw.length > 1 ? last.x - raw[raw.length - 2].x : 60 * 60 * 1000
  return [...raw, { x: last.x + interval - 1000, y: last.y }]
})

// shaded runs at or below (green) and above (red) the threshold
const priceAnnotations = computed<AnnotationOptions[]>(() => {
  if (props.modelValue === undefined || points.value.length === 0) return []
  const allowedColor = hexToRgba(getCssColor('--pv'), 0.2)
  const blockedColor = hexToRgba(getCssColor('--error'), 0.2)
  return priceRuns(points.value, props.modelValue).map((run) => ({
    type: 'box' as const,
    drawTime: 'beforeDatasetsDraw' as const,
    xMin: run.from,
    xMax: run.to,
    borderWidth: 1,
    borderColor: run.allowed ? allowedColor : blockedColor,
    backgroundColor: run.allowed ? allowedColor : blockedColor,
  }))
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

const chartOptions = computed<ChartOptions<'line'>>(() =>
  cardChartOptions({
    yTitle: 'Preis [ct/kWh]',
    noAnimation: true,
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
  }),
)

function onClick(event: MouseEvent): void {
  const chart = chartRef.value?.chart
  if (!chart) return
  const elements = chart.getElementsAtEventForMode(event, 'index', { intersect: false }, true)
  if (elements.length === 0) return
  const point = points.value[elements[0].index]
  if (point) emit('update:modelValue', Math.round(point.y * 100) / 100)
}
</script>
