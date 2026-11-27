<template>
  <div
    v-if="showFlow"
    class="panel relative mb-6 px-3 pt-4 pb-3 sm:px-6"
  >
    <FlowBalanceBar />
  </div>

  <div
    v-if="showChart"
    class="panel relative mb-6 px-3 pt-5 pb-4 sm:px-6"
  >
    <div class="mb-3 flex flex-wrap items-center justify-between gap-3">
      <div class="flex items-center gap-2">
        <h2 class="m-0 flex items-center gap-2 text-base font-bold">
          Verlauf
          ·
          <button
            type="button"
            class="cursor-pointer rounded-full border-0 px-2.5 py-1 text-[13px] font-semibold badge-muted"
            @click="mode = mode === 'day' ? 'live' : 'day'"
          >
            {{ mode === 'day' ? dayLabel : `Live · ${liveRangeMinutes} Min` }}
          </button>
        </h2>
        <template v-if="mode === 'day'">
          <BaseIconButton
            size="sm"
            aria-label="Vorheriger Tag"
            title="Vorheriger Tag"
            @click="goToPreviousDay"
          >
            <IconChevronLeft />
          </BaseIconButton>
          <BaseIconButton
            size="sm"
            :class="{ 'opacity-40': isToday }"
            aria-label="Nächster Tag"
            title="Nächster Tag"
            @click="goToNextDay"
          >
            <IconChevronRight />
          </BaseIconButton>
          <button
            v-if="!isToday"
            type="button"
            class="cursor-pointer rounded-full border-0 px-2 py-1 text-xs text-accent"
            @click="goToToday"
          >
            Heute
          </button>
          <div class="relative h-[22px] w-[22px] flex-none">
            <BaseIconButton
              size="sm"
              aria-label="Datum auswählen"
              title="Datum auswählen"
            >
              <IconCalendar />
            </BaseIconButton>
            <!-- transparent native date input over the icon button: the picker opens on click and the header row stays narrow -->
            <input
              type="date"
              aria-label="Datum auswählen"
              class="absolute inset-0 h-full w-full cursor-pointer opacity-0"
              :value="dateInputValue"
              :max="todayInputValue"
              @change="onDateInputChange"
            >
          </div>
        </template>
      </div>
      <div class="scrollbar-hide flex flex-nowrap items-center gap-4 overflow-x-auto sm:flex-wrap sm:overflow-visible">
        <button
          v-for="item in legend"
          :key="item.key"
          type="button"
          class="flex flex-none cursor-pointer items-center gap-1.5 border-0 bg-transparent p-0 text-[11px] whitespace-nowrap text-muted"
          :class="{ 'opacity-40': !item.visible }"
          @click="toggleLegendItem(item.key)"
        >
          <span
            class="legend-dot"
            :style="{ background: item.color }"
          />
          {{ item.label }}
        </button>
      </div>
    </div>

    <div class="relative min-h-[300px] sm:min-h-[420px]">
      <button
        v-if="isZoomed"
        class="absolute top-0 right-0 z-10 rounded-full border border-border bg-panel px-2.5 py-[3px] text-xs text-accent shadow-[0_2px_8px_rgba(0,0,0,0.1)]"
        type="button"
        @click="resetZoom"
      >
        Zoom zurücksetzen
      </button>
      <ChartjsLine
        v-if="hasData"
        :key="`${theme}-${mode}`"
        :data="chartData"
        :options="chartOptions"
        :plugins="[nowLabelPlugin]"
      />
      <p
        v-else-if="mode === 'day' && dayDenied"
        class="absolute inset-0 flex items-center justify-center px-4 text-center text-sm text-muted"
      >
        Für den Tagesverlauf fehlt die Berechtigung. Über die Schaltfläche oben lässt sich die Live-Ansicht wählen.
      </p>
      <div
        v-else-if="isLoading"
        class="absolute inset-0 flex items-center justify-center text-muted"
      >
        <IconRefresh class="animate-spin" />
      </div>
      <p
        v-else
        class="absolute inset-0 flex items-center justify-center text-sm text-muted"
      >
        {{ mode === 'day' ? 'Keine Daten für diesen Tag.' : 'Keine Daten für diesen Zeitraum.' }}
      </p>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed, ref, watch, watchEffect, onMounted, onUnmounted } from 'vue'
import { Line as ChartjsLine } from 'vue-chartjs'
import { Chart, type ChartOptions, type ChartData, type Plugin, type Scale } from 'chart.js'
import annotationPlugin from 'chartjs-plugin-annotation'
import zoomPlugin from 'chartjs-plugin-zoom'
import '@/utils/chartSetup'
import { useMqttStore } from '@/stores/mqtt-store'
import { useDailyLog } from '@/composables/useDailyLog'
import { useLiveView } from '@/composables/useLiveView'
import { useChartSettings, categoryDefs, type LegendKey } from '@/composables/useChartSettings'
import { getCssColor, hexToRgba, instanceColor } from '@/utils/color'
import { formatTooltipTime, formatChartDateLabel } from '@/utils/format'
import { roundTimeTicks, tickStepMinutes } from '@/utils/timeTicks'
import { categoryHasComponent } from '@/utils/categoryComponents'
import { alignDatasets } from '@/utils/alignDatasets'
import BaseIconButton from './BaseIconButton.vue'
import IconChevronLeft from './icons/IconChevronLeft.vue'
import IconChevronRight from './icons/IconChevronRight.vue'
import IconCalendar from './icons/IconCalendar.vue'
import IconRefresh from './icons/IconRefresh.vue'
import FlowBalanceBar from './FlowBalanceBar.vue'

Chart.register(annotationPlugin, zoomPlugin)

const {
  mode,
  showFlow,
  showChart,
  liveRangeMinutes,
  visibleSeries,
  categoryMode,
  forecastVisible,
  socVisibleSeries,
  socCategoryMode,
  isInstanceVisible,
  toggleLegendItem,
  categories: publishedCategories,
  batterySoc: publishedBatterySoc,
  selectedVehicleSoc: publishedSelectedVehicleSoc,
} = useChartSettings()

// kept in state: chartOptions is recomputed on every tick and would reset the zoomed bounds; clearing it is the reset (chart.resetZoom() would re-capture the range)
const zoomRange = ref<{ min: number; max: number } | null>(null)
const isZoomed = computed(() => zoomRange.value !== null)

// a forgotten zoom must not leave a stale view on an unattended screen
const ZOOM_AUTO_RESET_MS = 5 * 60 * 1000
let zoomResetTimer: ReturnType<typeof setTimeout> | undefined

function captureZoom(chart: Chart): void {
  const { min, max } = chart.scales.x
  zoomRange.value = { min, max }
  clearTimeout(zoomResetTimer)
  zoomResetTimer = setTimeout(resetZoom, ZOOM_AUTO_RESET_MS)
}

function timeAxisUnit(): 'minute' | 'hour' {
  const range = zoomRange.value ?? xRange.value
  return tickStepMinutes(range.max - range.min) ? 'minute' : 'hour'
}

function alignTimeTicks(scale: Scale): void {
  const step = tickStepMinutes(scale.max - scale.min)
  if (step) scale.ticks = roundTimeTicks(scale.min, scale.max, step).map((value) => ({ value }))
}

function resetZoom(): void {
  clearTimeout(zoomResetTimer)
  zoomRange.value = null
}

// Date.now() is not reactive; this ticks so the "now" line follows real time
const now = ref(Date.now())
let nowTimer: ReturnType<typeof setInterval> | undefined
onMounted(() => {
  nowTimer = setInterval(() => (now.value = Date.now()), 30_000)
})
onUnmounted(() => {
  clearInterval(nowTimer)
  clearTimeout(zoomResetTimer)
})

// Chart.js options are JS, not CSS, so the narrow layout needs a viewport check here
const isNarrow = ref(window.innerWidth < 640)
function updateIsNarrow(): void {
  isNarrow.value = window.innerWidth < 640
}
onMounted(() => window.addEventListener('resize', updateIsNarrow))
onUnmounted(() => window.removeEventListener('resize', updateIsNarrow))

// drawn manually: the annotation plugin's own label kept getting clipped
const nowLabelPlugin: Plugin<'line'> = {
  id: 'nowLabel',
  afterDraw(chart) {
    // only meaningful in the day view of today
    if (mode.value !== 'day' || !isToday.value) return
    const x = chart.scales.x?.getPixelForValue(now.value)
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

// without chart rights the daily log is never delivered
const dayDenied = computed(
  () => mqttStore.userManagementKnown() && mqttStore.userManagementActive() && !mqttStore.accessChartAllowed(),
)
const dayFetchEnabled = computed(() => mode.value === 'day' && mqttStore.userManagementKnown() && !dayDenied.value)

const {
  categories: dayCategories,
  batterySoc: dayBatterySoc,
  vehicleSocAll: dayVehicleSocAll,
  forecast: dayForecast,
  isLoading: dayIsLoading,
  selectedDate,
  isToday,
  goToPreviousDay,
  goToNextDay,
  goToToday,
  goToDate,
} = useDailyLog(dayFetchEnabled)
const dayLabel = computed(() => formatChartDateLabel(selectedDate.value))

// <input type="date"> uses YYYY-MM-DD regardless of locale
function toDateInputValue(date: Date): string {
  return `${date.getFullYear()}-${(date.getMonth() + 1).toString().padStart(2, '0')}-${date
    .getDate()
    .toString()
    .padStart(2, '0')}`
}
const dateInputValue = computed(() => toDateInputValue(selectedDate.value))
const todayInputValue = computed(() => toDateInputValue(new Date()))
function onDateInputChange(event: Event): void {
  const value = (event.target as HTMLInputElement).value
  if (!value) return
  const [year, month, day] = value.split('-').map(Number)
  goToDate(new Date(year, month - 1, day))
}
const {
  categories: liveCategories,
  batterySoc: liveBatterySoc,
  vehicleSocAll: liveVehicleSocAll,
} = useLiveView(liveRangeMinutes)
const categories = computed(() => (mode.value === 'live' ? liveCategories.value : dayCategories.value))
const batterySoc = computed(() => (mode.value === 'live' ? liveBatterySoc.value : dayBatterySoc.value))
const vehicleSocAll = computed(() => (mode.value === 'live' ? liveVehicleSocAll.value : dayVehicleSocAll.value))
// at most 2, connected vehicles first
const selectedVehicleSoc = computed(() =>
  mqttStore.topVehicleIds
    .map((id) => vehicleSocAll.value.find((v) => v.id === String(id)))
    .filter((v): v is NonNullable<typeof v> => v !== undefined)
    .map((v) => ({ ...v, label: mqttStore.vehicleList.find((veh) => veh.id === Number(v.id))?.name ?? v.label })),
)

// unlike the day view there is no response signal: a short grace period for the broker to redeliver the retained chunks
const liveIsLoading = ref(false)
let liveLoadingTimeout: ReturnType<typeof setTimeout> | undefined
function startLiveLoadingGracePeriod(): void {
  liveIsLoading.value = true
  clearTimeout(liveLoadingTimeout)
  liveLoadingTimeout = setTimeout(() => {
    liveIsLoading.value = false
  }, 5000)
}
watch(liveCategories, () => {
  if (liveCategories.value.grid.all.length > 0) liveIsLoading.value = false
})

// the persisted mode can already be 'live' on load
if (mode.value === 'live') {
  mqttStore.subscribeLiveSeries()
  startLiveLoadingGracePeriod()
}

// the live feed is only subscribed while the live view is shown; selecting it resets the range to the maximum
watch(mode, (m) => {
  if (m === 'live') {
    mqttStore.subscribeLiveSeries()
    startLiveLoadingGracePeriod()
    liveRangeMinutes.value = 120
  } else {
    mqttStore.unsubscribeLiveSeries()
    clearTimeout(liveLoadingTimeout)
  }
})
onUnmounted(() => {
  if (mode.value === 'live') mqttStore.unsubscribeLiveSeries()
  clearTimeout(liveLoadingTimeout)
})

watch([mode, selectedDate], resetZoom)

const hasData = computed(() => categories.value.grid.all.length > 0)
const isLoading = computed(() => (mode.value === 'live' ? liveIsLoading.value : dayIsLoading.value))

// published for ThemeSettingsModal, which sits elsewhere in the tree and needs the same lines
watchEffect(() => {
  publishedCategories.value = categories.value
  publishedBatterySoc.value = batterySoc.value
  publishedSelectedVehicleSoc.value = selectedVehicleSoc.value
})

// whole-day forecast: today from the live topic, past days from the value each log entry carried at its time
const forecastSeriesDay = computed(() => {
  if (mode.value !== 'day' || categoryMode.pv !== 'combined') return []
  let raw: { x: number; y: number }[]
  if (!isToday.value) {
    // entries without a logged forecast are missing, like for a system switched on mid-day
    raw = dayForecast.value.map((entry) => ({ x: entry.timestamp, y: entry.power }))
  } else {
    if (!mqttStore.forecastConfigured) return []
    const startOfToday = new Date().setHours(0, 0, 0, 0)
    const endOfToday = new Date().setHours(23, 59, 59, 999)
    raw = mqttStore.forecastSeries
      .filter((entry) => entry.timestamp >= startOfToday && entry.timestamp <= endOfToday)
      .map((entry) => ({ x: entry.timestamp, y: entry.power }))
  }
  return raw
})
const forecastDay = computed(() => (forecastVisible.value ? forecastSeriesDay.value : []))

const visibleCategoryDefs = computed(() =>
  categoryDefs.filter((c) => categoryHasComponent(c.key, mqttStore, categories.value.counter.individual.length)),
)

const legend = computed(() => {
  void props.theme
  const items = visibleCategoryDefs.value.map((c) => ({
    key: c.key as LegendKey,
    label: c.label,
    color: getCssColor(c.colorVar),
    visible: visibleSeries[c.key],
  }))
  if (forecastSeriesDay.value.length > 1) {
    items.push({ key: 'forecast', label: 'Prognose', color: getCssColor('--pv'), visible: forecastVisible.value })
  }
  if (batterySoc.value.all.length > 0) {
    items.push({ key: 'batterySoc', label: 'Speicher-SoC', color: getCssColor('--battery'), visible: socVisibleSeries.batterySoc })
  }
  if (selectedVehicleSoc.value.length > 0) {
    const label = selectedVehicleSoc.value.length === 1 ? selectedVehicleSoc.value[0].label : 'Fahrzeug-SoC'
    items.push({ key: 'vehicleSoc', label, color: getCssColor('--car'), visible: socVisibleSeries.vehicleSoc })
  }
  return items
})

// day view: the whole day. Live: from the earliest held point, so the axis grows with the data instead of showing an empty gap
const xRange = computed(() => {
  if (mode.value === 'live') {
    const windowStart = now.value - liveRangeMinutes.value * 60 * 1000
    const earliest = categories.value.grid.all[0]?.timestamp
    return { min: earliest !== undefined ? Math.max(earliest, windowStart) : windowStart, max: now.value }
  }
  return {
    min: new Date(selectedDate.value).setHours(0, 0, 0, 0),
    max: new Date(selectedDate.value).setHours(23, 59, 59, 999),
  }
})

const chartData = computed<ChartData<'line', { x: number; y: number }[]>>(() => {
  void props.theme
  const datasets: ChartData<'line', { x: number; y: number }[]>['datasets'] = []

  categoryDefs.forEach((cat) => {
    if (!visibleSeries[cat.key]) return
    const data = categories.value[cat.key]
    const useIndividual = categoryMode[cat.key] === 'individual' && data.individual.length > 0

    if (useIndividual) {
      data.individual.forEach((inst, idx) => {
        if (!isInstanceVisible(cat.key, inst.id)) return
        const color = instanceColor(getCssColor(cat.colorVar), idx)
        datasets.push({
          label: inst.label,
          data: inst.points.map((p) => ({ x: p.timestamp, y: p.power })),
          borderColor: color,
          backgroundColor: hexToRgba(color, 0.12),
          fill: true,
          borderWidth: 1.25,
          pointRadius: 0,
          tension: 0.2,
        })
      })
    } else {
      const color = getCssColor(cat.colorVar)
      datasets.push({
        label: cat.label,
        data: data.all.map((p) => ({ x: p.timestamp, y: p.power })),
        borderColor: color,
        backgroundColor: hexToRgba(color, 0.18),
        fill: true,
        borderWidth: 1.25,
        pointRadius: 0,
        tension: 0.2,
      })
    }
  })

  const forecastDatasets = new Set<(typeof datasets)[number]>()
  if (forecastDay.value.length > 1) {
    const pvColor = getCssColor('--pv')
    const forecast = {
      label: 'Prognose',
      data: forecastDay.value,
      borderColor: pvColor,
      backgroundColor: 'transparent',
      fill: false,
      borderWidth: 1.5,
      pointRadius: 0,
      tension: 0.2,
      borderDash: [6, 6],
    }
    datasets.push(forecast)
    forecastDatasets.add(forecast)
  }

  // finer than the forecast dash so both read differently
  const SOC_DASH = [3, 3]

  if (socVisibleSeries.batterySoc) {
    const useIndividual = socCategoryMode.batterySoc === 'individual' && batterySoc.value.individual.length > 0
    if (useIndividual) {
      batterySoc.value.individual.forEach((inst, idx) => {
        if (!isInstanceVisible('batterySoc', inst.id)) return
        datasets.push({
          label: inst.label,
          data: inst.points.map((p) => ({ x: p.timestamp, y: p.soc })),
          borderColor: instanceColor(getCssColor('--battery'), idx),
          backgroundColor: 'transparent',
          fill: false,
          borderWidth: 1.5,
          pointRadius: 0,
          tension: 0.2,
          borderDash: SOC_DASH,
          yAxisID: 'y1',
        })
      })
    } else if (batterySoc.value.all.length > 0) {
      datasets.push({
        label: 'Speicher-SoC',
        data: batterySoc.value.all.map((p) => ({ x: p.timestamp, y: p.soc })),
        borderColor: getCssColor('--battery'),
        backgroundColor: 'transparent',
        fill: false,
        borderWidth: 1.5,
        pointRadius: 0,
        tension: 0.2,
        borderDash: SOC_DASH,
        yAxisID: 'y1',
      })
    }
  }
  if (socVisibleSeries.vehicleSoc) {
    selectedVehicleSoc.value.forEach((v, idx) => {
      if (!isInstanceVisible('vehicleSoc', v.id)) return
      datasets.push({
        label: v.label,
        data: v.points.map((p) => ({ x: p.timestamp, y: p.soc })),
        borderColor: instanceColor(getCssColor('--car'), idx),
        backgroundColor: 'transparent',
        fill: false,
        borderWidth: 1.5,
        pointRadius: 0,
        tension: 0.2,
        borderDash: SOC_DASH,
        yAxisID: 'y1',
      })
    })
  }
  return { datasets: alignDatasets(datasets, forecastDatasets) }
})

const chartOptions = computed<ChartOptions<'line'>>(() => {
  void props.theme
  const mutedColor = getCssColor('--muted')
  const borderColor = getCssColor('--border')
  const panelColor = getCssColor('--panel')
  const textColor = getCssColor('--text')
  return {
    responsive: true,
    maintainAspectRatio: false,
    // live mode redraws every cycle; the default transition showed a wipe flash
    animation: false,
    layout: { padding: { top: 20 } },
    interaction: { mode: 'index', intersect: false },
    plugins: {
      legend: { display: false },
      tooltip: {
        enabled: true,
        // Chart.js' default tooltip is dark regardless of the theme
        backgroundColor: panelColor,
        titleColor: textColor,
        bodyColor: textColor,
        borderColor,
        borderWidth: 1,
        padding: 8,
        cornerRadius: 8,
        filter: (item) => Number.isFinite(item.parsed.y),
        callbacks: {
          title: (items) => {
            const x = items[0]?.parsed.x
            return typeof x === 'number' ? formatTooltipTime(x, mode.value === 'live') : ''
          },
        },
      },
      annotation: {
        annotations: {
          now: {
            type: 'line',
            display: mode.value === 'day' && isToday.value,
            xMin: now.value,
            xMax: now.value,
            borderColor: mutedColor,
            borderWidth: 1.5,
            borderDash: [3, 4],
          },
        },
      },
      zoom: {
        limits: {
          x: { min: xRange.value.min, max: xRange.value.max, minRange: 5 * 60 * 1000 },
        },
        // no drag-to-pan on narrow screens: it blocks scrolling past the chart (pinch still works)
        pan: { enabled: !isNarrow.value, mode: 'x', onPanComplete: ({ chart }) => captureZoom(chart) },
        zoom: {
          wheel: { enabled: true },
          pinch: { enabled: true },
          mode: 'x',
          onZoomComplete: ({ chart }) => captureZoom(chart),
        },
      },
    },
    scales: {
      x: {
        type: 'time',
        min: zoomRange.value?.min ?? xRange.value.min,
        max: zoomRange.value?.max ?? xRange.value.max,
        time: { unit: timeAxisUnit() },
        afterBuildTicks: alignTimeTicks,
        grid: { color: borderColor },
        ticks: { color: mutedColor, font: { size: 11 } },
      },
      y: {
        suggestedMin: 0,
        grid: { color: borderColor },
        ticks: { color: mutedColor, font: { size: isNarrow.value ? 10 : 12 } },
        title: { display: !isNarrow.value, text: 'Leistung [kW]', color: mutedColor, font: { size: 12 } },
      },
      y1: {
        position: 'right',
        min: 0,
        max: 100,
        // no gridlines of its own: they would not line up with the left axis
        grid: { display: false },
        ticks: {
          color: mutedColor,
          font: { size: isNarrow.value ? 10 : 12 },
          callback: (value) => `${value}%`,
        },
        title: { display: !isNarrow.value, text: 'SoC [%]', color: mutedColor, font: { size: 12 } },
      },
    },
  }
})
</script>
