<template>
  <div
    v-if="showFlow"
    class="panel relative mb-6 px-3 pt-4 pb-3 sm:px-6"
  >
    <h2 class="m-0 mb-2 text-base font-bold">
      <span v-if="displayMode === 'both'">Fluss</span>
      <button
        v-else
        type="button"
        class="cursor-pointer border-0 bg-transparent p-0 font-bold text-text"
        title="Zwischen Diagramm und Fluss-Ansicht wechseln"
        @click="displayMode = 'chart'"
      >
        Fluss
      </button>
    </h2>
    <FlowBalanceBar />
  </div>

  <div
    v-if="showChart"
    class="panel relative mb-6 px-3 pt-5 pb-4 sm:px-6"
  >
    <div class="mb-3 flex flex-wrap items-center justify-between gap-3">
      <div class="flex items-center gap-2">
        <h2 class="m-0 flex items-center gap-2 text-base font-bold">
          <span v-if="displayMode === 'both'">Verlauf</span>
          <button
            v-else
            type="button"
            class="cursor-pointer border-0 bg-transparent p-0 font-bold text-text"
            title="Zwischen Diagramm und Fluss-Ansicht wechseln"
            @click="displayMode = 'flow'"
          >
            Verlauf
          </button>
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
            <!-- transparent native date input overlaid on the icon button - clicking anywhere on
                 it opens the browser's own date picker, so the visible chip stays icon-only and
                 doesn't widen the header row (a full-width input here used to push the legend
                 onto its own line). The date itself is already shown by the dayLabel pill above. -->
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
        ref="chartRef"
        :key="`${theme}-${mode}`"
        :data="chartData"
        :options="chartOptions"
        :plugins="[nowLabelPlugin]"
      />
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
import { Chart, type ChartOptions, type ChartData, type Plugin } from 'chart.js'
import annotationPlugin from 'chartjs-plugin-annotation'
import zoomPlugin from 'chartjs-plugin-zoom'
import '@/utils/chartSetup'
import { useMqttStore } from '@/stores/mqtt-store'
import { useDailyLog } from '@/composables/useDailyLog'
import { useLiveView } from '@/composables/useLiveView'
import { useChartSettings, categoryDefs, type LegendKey } from '@/composables/useChartSettings'
import { getCssColor, hexToRgba, instanceColor } from '@/utils/color'
import { formatTooltipTime, formatChartDateLabel } from '@/utils/format'
import type { CategoryKey } from '@/types/chart'
import BaseIconButton from './BaseIconButton.vue'
import IconChevronLeft from './icons/IconChevronLeft.vue'
import IconChevronRight from './icons/IconChevronRight.vue'
import IconCalendar from './icons/IconCalendar.vue'
import IconRefresh from './icons/IconRefresh.vue'
import FlowBalanceBar from './FlowBalanceBar.vue'

Chart.register(annotationPlugin, zoomPlugin)

const {
  mode,
  displayMode,
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

const showChart = computed(() => displayMode.value !== 'flow')
const showFlow = computed(() => displayMode.value !== 'chart')

const chartRef = ref<{ chart?: Chart } | null>(null)
const isZoomed = ref(false)

function resetZoom(): void {
  chartRef.value?.chart?.resetZoom()
  isZoomed.value = false
}

// Date.now() isn't a reactive dependency, so without this, 'now' (the chart options
// computed's xMin/xMax for the vertical line) would freeze at whatever moment the
// component happened to last recompute, instead of tracking real time
const now = ref(Date.now())
let nowTimer: ReturnType<typeof setInterval> | undefined
onMounted(() => {
  nowTimer = setInterval(() => (now.value = Date.now()), 30_000)
})
onUnmounted(() => clearInterval(nowTimer))

// Chart.js options are JS-driven, not CSS - this is the one piece of the axis chrome that needs
// a real viewport check rather than a Tailwind breakpoint class, to drop the rotated axis titles
// and shrink the tick font on narrow screens, where both eat real width from the already-short plot area
const isNarrow = ref(window.innerWidth < 640)
function updateIsNarrow(): void {
  isNarrow.value = window.innerWidth < 640
}
onMounted(() => window.addEventListener('resize', updateIsNarrow))
onUnmounted(() => window.removeEventListener('resize', updateIsNarrow))

// drawn manually instead of via chartjs-plugin-annotation's own label - that label kept
// getting clipped against the chart area regardless of position/yAdjust/clip settings
const nowLabelPlugin: Plugin<'line'> = {
  id: 'nowLabel',
  afterDraw(chart) {
    // not useful in live mode ("now" already sits right at the chart's right edge there), nor
    // when viewing a past day (there's no "now" within that day's range)
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
} = useDailyLog()
const dayLabel = computed(() => formatChartDateLabel(selectedDate.value))

// native <input type="date"> uses the fixed YYYY-MM-DD format regardless of locale, unlike
// dateToString's YYYYMMDD (built for the MQTT topic, not for this input)
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
// at most 2, prioritized by mqttStore.topVehicleIds (connected-to-a-chargepoint first)
const selectedVehicleSoc = computed(() =>
  mqttStore.topVehicleIds
    .map((id) => vehicleSocAll.value.find((v) => v.id === String(id)))
    .filter((v): v is NonNullable<typeof v> => v !== undefined)
    .map((v) => ({ ...v, label: mqttStore.vehicleList.find((veh) => veh.id === Number(v.id))?.name ?? v.label })),
)

// live mode has no equivalent of day mode's guaranteed command-response signal (graph.py's
// retained alllivevaluesJson* chunks only exist once something has actually been logged, which a
// fresh install genuinely may not have yet) - so this is a short grace period after
// (re-)subscribing, just long enough for the broker to redeliver the retained chunks, rather than
// a precise "response received" check
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

// mode can start as 'live' on a reload (persisted) - the watch below only reacts to later
// changes, so the initial subscription needs its own call here
if (mode.value === 'live') {
  mqttStore.subscribeLiveSeries()
  startLiveLoadingGracePeriod()
}

// the alllivevaluesJson* feed is only worth subscribing to while live view is actually shown;
// default the range back to the max each time live is (re-)selected
watch(mode, (m) => {
  if (m === 'live') {
    mqttStore.subscribeLiveSeries()
    startLiveLoadingGracePeriod()
    liveRangeMinutes.value = 120
  } else {
    mqttStore.unsubscribeLiveSeries()
    clearTimeout(liveLoadingTimeout)
  }
  isZoomed.value = false
})
onUnmounted(() => {
  if (mode.value === 'live') mqttStore.unsubscribeLiveSeries()
  clearTimeout(liveLoadingTimeout)
})

// a zoom/pan from a previously viewed day shouldn't carry over to the newly selected one
watch(selectedDate, () => (isZoomed.value = false))

const hasData = computed(() => categories.value.grid.all.length > 0)
const isLoading = computed(() => (mode.value === 'live' ? liveIsLoading.value : dayIsLoading.value))

// published so ThemeSettingsModal.vue (a sibling, not a child - rendered from the hamburger
// menu in App.vue) can show "which categories/instances exist right now" in its "Linien"
// section without independently re-subscribing to the daily-log/live-view feeds itself
watchEffect(() => {
  publishedCategories.value = categories.value
  publishedBatterySoc.value = batterySoc.value
  publishedSelectedVehicleSoc.value = selectedVehicleSoc.value
})

// Chart.js' 'index' tooltip mode (interaction.mode below) matches datasets by shared ARRAY
// POSITION, not shared x-value - fine when every dataset has the same points (all the day-mode
// power/SoC categories do, since they're all built from the same daily_log entries), but forecast
// comes from a separate, much coarser-sampled feed. Left unaligned, the tooltip would show
// forecast's value from whatever index the dense categories happen to be at, i.e. essentially a
// random nearby forecast point - frequently landing on a night-time (zero) entry since those
// dominate the array, which is exactly the "always shows 0" bug reported. Resampling onto the
// same timestamps every other day-mode series already shares fixes this at the root instead of
// patching the tooltip display after the fact.
function resampleToTimestamps(points: { x: number; y: number }[], timestamps: number[]): { x: number; y: number }[] {
  if (points.length === 0) return []
  let i = 0
  return timestamps.map((t) => {
    while (i < points.length - 2 && points[i + 1].x <= t) i++
    const a = points[i]
    const b = points[i + 1]
    if (!b || t <= a.x) return { x: t, y: a.y }
    if (t >= b.x) return { x: t, y: b.y }
    const ratio = (t - a.x) / (b.x - a.x)
    return { x: t, y: a.y + (b.y - a.y) * ratio }
  })
}

// whole-day forecast for the day currently selected in day mode. Today, unchanged from before:
// the live MQTT snapshot (mqttStore.forecastSeries), the continuously-refining forecast for a day
// that hasn't ended yet. Past days instead read the daily_log's own "forecast" field (see
// write_log.py::get_forecast_values), a snapshot frozen once that day ended - the live topic has
// long since moved on to today's values by then, so it's the only source history can use; older
// days (or days forecast wasn't configured for) simply have none. History can be flat/missing
// (component in error state) while the forecast is already known in full; only meaningful next to
// the day view's combined PV line.
// Split from forecastDay (the actually-drawn series) so the legend item can stay present and
// clickable even while forecastVisible is off - otherwise toggling it hides the only way back on.
const forecastSeriesDay = computed(() => {
  if (mode.value !== 'day' || categoryMode.pv !== 'combined') return []
  if (!isToday.value) return dayForecast.value.map((entry) => ({ x: entry.timestamp, y: entry.power }))
  if (!mqttStore.forecastConfigured) return []
  const startOfToday = new Date().setHours(0, 0, 0, 0)
  const endOfToday = new Date().setHours(23, 59, 59, 999)
  const raw = mqttStore.forecastSeries
    .filter((entry) => entry.timestamp >= startOfToday && entry.timestamp <= endOfToday)
    .map((entry) => ({ x: entry.timestamp, y: entry.power }))
  // only resample the elapsed portion (where real power data exists and needs shared-index
  // tooltip alignment) - grid.all has no entries for the future, so resampling the whole series
  // onto it would silently cut the forecast off at "now" instead of showing the rest of the day.
  // grid.all also doesn't necessarily start at 00:00 (e.g. a system only switched on at 13:00
  // that day has no log entries before that) - any forecast points before its first timestamp need
  // to be kept unchanged too, same as the future tail, or they'd be silently dropped instead of
  // showing the pre-startup projected line
  const referenceTimestamps = categories.value.grid.all.map((p) => p.timestamp)
  if (referenceTimestamps.length === 0) return raw
  const firstReference = referenceTimestamps[0]
  const lastReference = referenceTimestamps[referenceTimestamps.length - 1]
  const past = raw.filter((p) => p.x < firstReference)
  const resampledElapsed = resampleToTimestamps(raw, referenceTimestamps)
  const future = raw.filter((p) => p.x > lastReference)
  return [...past, ...resampledElapsed, ...future]
})
const forecastDay = computed(() => (forecastVisible.value ? forecastSeriesDay.value : []))

// whether a category has any real component behind it at all - grid/house are always
// meaningful (grid connection + derived house consumption always exist), the rest depend on
// what's actually configured. 'counter' has no static hierarchy signal (grid vs. non-grid is a
// runtime flag, not a hierarchy-level distinction), so it reads the live category data instead.
function categoryHasComponent(key: CategoryKey): boolean {
  switch (key) {
    case 'grid':
    case 'house':
      return true
    case 'pv':
      return mqttStore.inverterIds.length > 0
    case 'battery':
      return mqttStore.batteryIds.length > 0
    case 'chargepoint':
      return mqttStore.chargePointIds.length > 0
    case 'consumer':
      return mqttStore.consumerIds.length > 0
    case 'counter':
      return categories.value.counter.individual.length > 0
  }
}

const visibleCategoryDefs = computed(() => categoryDefs.filter((c) => categoryHasComponent(c.key)))

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

// x-axis bounds: the whole day for the day view, or the selected rolling window for live view
const xRange = computed(() => {
  if (mode.value === 'live') {
    return { min: now.value - liveRangeMinutes.value * 60 * 1000, max: now.value }
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
          // lighter than the combined-mode fill (0.18) since individual instances can overlap
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

  if (forecastDay.value.length > 1) {
    const pvColor = getCssColor('--pv')
    datasets.push({
      label: 'Prognose',
      data: forecastDay.value,
      borderColor: pvColor,
      backgroundColor: 'transparent',
      fill: false,
      borderWidth: 1.5,
      pointRadius: 0,
      tension: 0.2,
      borderDash: [6, 6],
    })
  }

  // dash pattern deliberately finer than the forecast line's [6, 6] - both can be on screen at
  // once and need to read as different lines at a glance, not just different colors
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
  return { datasets }
})

const chartOptions = computed<ChartOptions<'line'>>(() => {
  void props.theme
  const mutedColor = getCssColor('--muted')
  const borderColor = getCssColor('--border')
  return {
    responsive: true,
    maintainAspectRatio: false,
    // live mode re-fetches/re-renders every MQTT cycle (~10s) - Chart.js' default transition
    // animation on each .update() call produced a visible diagonal "wipe" flash across the filled
    // areas every tick, since points reposition on the sliding x-axis window at the same time.
    animation: false,
    layout: { padding: { top: 20 } },
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
        // disabled on narrow/touch viewports - a single-finger drag-to-pan there captures every
        // attempt to scroll the page past the chart, which is far more disruptive than losing pan
        // (pinch-zoom, a deliberate 2-finger gesture that doesn't conflict with scrolling, still works)
        pan: { enabled: !isNarrow.value, mode: 'x', onPanComplete: () => (isZoomed.value = true) },
        zoom: {
          wheel: { enabled: true },
          pinch: { enabled: true },
          mode: 'x',
          onZoomComplete: () => (isZoomed.value = true),
        },
      },
    },
    scales: {
      x: {
        type: 'time',
        min: xRange.value.min,
        max: xRange.value.max,
        time: { unit: mode.value === 'live' ? 'minute' : 'hour' },
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
        // no own gridlines - sharing the left axis' would double up at mismatched tick spacing
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
