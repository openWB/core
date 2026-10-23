<template>
  <div
    class="panel"
    style="padding: 20px 24px 16px; margin-bottom: 24px"
  >
    <div style="display: flex; align-items: center; justify-content: space-between; flex-wrap: wrap; gap: 12px; margin-bottom: 12px">
      <div style="display: flex; align-items: center; gap: 8px">
        <h2 style="margin: 0; font-size: 16px; font-weight: 700">
          Verlauf &middot; {{ mode === 'day' ? 'Heute' : `Live · ${liveRangeMinutes} Min` }}
        </h2>
        <div style="position: relative">
          <BaseIconButton
            aria-label="Diagramm-Einstellungen"
            @click="showSettings = !showSettings"
          >
            <IconGear />
          </BaseIconButton>
          <div
            v-if="showSettings"
            class="settings-backdrop"
            @click="showSettings = false"
          />
          <div
            v-if="showSettings"
            class="settings-panel panel"
          >
            <div class="settings-group-label">
              Ansicht
            </div>
            <BaseTabGroup
              dense
              :model-value="mode"
              :options="viewOptions"
              @update="mode = $event"
            />

            <template v-if="mode === 'live'">
              <div class="settings-group-label">
                Zeitfenster &middot; {{ liveRangeMinutes }} Min
              </div>
              <input
                v-model.number="liveRangeMinutes"
                class="range-slider"
                type="range"
                min="15"
                max="120"
                step="15"
              >
            </template>

            <div class="settings-group-label">
              Linien
            </div>
            <div
              v-for="cat in categoryDefs"
              :key="cat.key"
              class="category-block"
            >
              <label class="series-toggle">
                <input
                  v-model="visibleSeries[cat.key]"
                  type="checkbox"
                >
                <span
                  class="legend-dot"
                  :style="{ background: getCssColor(cat.colorVar) }"
                />
                {{ cat.label }}
              </label>

              <div
                v-if="visibleSeries[cat.key] && categories[cat.key].individual.length > 0"
                class="category-mode-row"
              >
                <BaseTabGroup
                  dense
                  :model-value="categoryMode[cat.key]"
                  :options="categoryModeOptions"
                  @update="categoryMode[cat.key] = $event"
                />
              </div>

              <div
                v-if="visibleSeries[cat.key] && categoryMode[cat.key] === 'individual' && categories[cat.key].individual.length > 0"
                class="instance-list"
              >
                <label
                  v-for="(inst, idx) in categories[cat.key].individual"
                  :key="inst.id"
                  class="series-toggle instance-toggle"
                >
                  <input
                    type="checkbox"
                    :checked="isInstanceVisible(cat.key, inst.id)"
                    @change="setInstanceVisible(cat.key, inst.id, ($event.target as HTMLInputElement).checked)"
                  >
                  <span
                    class="legend-dot"
                    :style="{ background: instanceColor(getCssColor(cat.colorVar), idx) }"
                  />
                  {{ inst.label }}
                </label>
              </div>
            </div>
          </div>
        </div>
      </div>
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
        <button
          v-if="isZoomed"
          class="reset-zoom-btn"
          type="button"
          @click="resetZoom"
        >
          Zoom zurücksetzen
        </button>
      </div>
    </div>

    <div style="min-height: 420px">
      <ChartjsLine
        v-if="hasData"
        ref="chartRef"
        :key="`${theme}-${mode}`"
        :data="chartData"
        :options="chartOptions"
        :plugins="[nowLabelPlugin]"
      />
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed, reactive, ref, watch, watchEffect, onMounted, onUnmounted } from 'vue'
import { Line as ChartjsLine } from 'vue-chartjs'
import { Chart, type ChartOptions, type ChartData, type Plugin } from 'chart.js'
import annotationPlugin from 'chartjs-plugin-annotation'
import zoomPlugin from 'chartjs-plugin-zoom'
import '@/utils/chartSetup'
import { useMqttStore } from '@/stores/mqtt-store'
import { useDailyLog } from '@/composables/useDailyLog'
import { useLiveView } from '@/composables/useLiveView'
import { getCssColor, hexToRgba, instanceColor } from '@/utils/color'
import { formatTooltipTime } from '@/utils/format'
import type { CategoryKey } from '@/types/chart'
import IconGear from './icons/IconGear.vue'
import BaseIconButton from './BaseIconButton.vue'
import BaseTabGroup from './BaseTabGroup.vue'

Chart.register(annotationPlugin, zoomPlugin)

const viewOptions = [
  { value: 'day', label: 'Heute' },
  { value: 'live', label: 'Live' },
] as const
const categoryModeOptions = [
  { value: 'combined', label: 'Gesamt' },
  { value: 'individual', label: 'Einzeln' },
] as const

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

// drawn manually instead of via chartjs-plugin-annotation's own label - that label kept
// getting clipped against the chart area regardless of position/yAdjust/clip settings
const nowLabelPlugin: Plugin<'line'> = {
  id: 'nowLabel',
  afterDraw(chart) {
    // not useful in live mode - "now" already sits right at the chart's right edge there
    if (mode.value !== 'day') return
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

interface PersistedChartSettings {
  mode?: 'day' | 'live'
  liveRangeMinutes?: number
  visibleSeries?: Partial<Record<CategoryKey, boolean>>
  categoryMode?: Partial<Record<CategoryKey, 'combined' | 'individual'>>
  instanceVisibility?: Record<string, boolean>
}

const STORAGE_KEY = 'quartz-chart-settings'

function loadPersistedSettings(): PersistedChartSettings {
  try {
    const raw = localStorage.getItem(STORAGE_KEY)
    return raw ? (JSON.parse(raw) as PersistedChartSettings) : {}
  } catch {
    return {}
  }
}

const persisted = loadPersistedSettings()

const showSettings = ref(false)
const mode = ref<'day' | 'live'>(persisted.mode ?? 'day')
const liveRangeMinutes = ref(persisted.liveRangeMinutes ?? 120)

const { categories: dayCategories } = useDailyLog()
const { categories: liveCategories } = useLiveView(liveRangeMinutes)
const categories = computed(() => (mode.value === 'live' ? liveCategories.value : dayCategories.value))

// mode can start as 'live' on a reload (persisted) - the watch below only reacts to later
// changes, so the initial subscription needs its own call here
if (mode.value === 'live') mqttStore.subscribeLiveSeries()

// the alllivevaluesJson* feed is only worth subscribing to while live view is actually shown;
// default the range back to the max each time live is (re-)selected
watch(mode, (m) => {
  if (m === 'live') {
    mqttStore.subscribeLiveSeries()
    liveRangeMinutes.value = 120
  } else {
    mqttStore.unsubscribeLiveSeries()
  }
  isZoomed.value = false
})
onUnmounted(() => {
  if (mode.value === 'live') mqttStore.unsubscribeLiveSeries()
})

const hasData = computed(() => categories.value.grid.all.length > 0)

interface CategoryDef {
  key: CategoryKey
  label: string
  colorVar: string
  fill: boolean
}

const categoryDefs: CategoryDef[] = [
  { key: 'pv', label: 'Erzeugung', colorVar: '--pv', fill: true },
  { key: 'house', label: 'Hausverbrauch', colorVar: '--consumption', fill: false },
  { key: 'grid', label: 'Netz', colorVar: '--grid', fill: false },
  { key: 'battery', label: 'Speicher', colorVar: '--battery', fill: false },
  { key: 'chargepoint', label: 'Ladepunkte', colorVar: '--chargepoint', fill: false },
  { key: 'consumer', label: 'Verbraucher', colorVar: '--consumer', fill: false },
]

const visibleSeries = reactive<Record<CategoryKey, boolean>>({
  pv: true,
  house: true,
  grid: true,
  battery: true,
  chargepoint: true,
  consumer: true,
  ...persisted.visibleSeries,
})

const categoryMode = reactive<Record<CategoryKey, 'combined' | 'individual'>>({
  pv: 'combined',
  house: 'combined',
  grid: 'combined',
  battery: 'combined',
  chargepoint: 'combined',
  consumer: 'combined',
  ...persisted.categoryMode,
})

// per-instance visibility within "Einzeln" mode, keyed "<category>:<instanceId>" - defaults to
// visible so a newly-appeared component shows up without the user having to opt it in
const instanceVisibility = reactive<Record<string, boolean>>({ ...persisted.instanceVisibility })

watchEffect(() => {
  const settings: PersistedChartSettings = {
    mode: mode.value,
    liveRangeMinutes: liveRangeMinutes.value,
    visibleSeries: { ...visibleSeries },
    categoryMode: { ...categoryMode },
    instanceVisibility: { ...instanceVisibility },
  }
  try {
    localStorage.setItem(STORAGE_KEY, JSON.stringify(settings))
  } catch {
    // ignore storage errors (private browsing etc.)
  }
})

function isInstanceVisible(category: CategoryKey, id: string): boolean {
  return instanceVisibility[`${category}:${id}`] ?? true
}
function setInstanceVisible(category: CategoryKey, id: string, visible: boolean): void {
  instanceVisibility[`${category}:${id}`] = visible
}

// whole-day forecast, independent of how much real history exists - history can be
// flat/missing (component in error state, or just started) while the forecast for
// today is already known in full; only meaningful next to the day view's combined PV line
const forecastToday = computed(() => {
  if (mode.value !== 'day' || !visibleSeries.pv || categoryMode.pv !== 'combined' || !mqttStore.forecastConfigured) {
    return []
  }
  const startOfToday = new Date().setHours(0, 0, 0, 0)
  const endOfToday = new Date().setHours(23, 59, 59, 999)
  return mqttStore.forecastSeries
    .filter((entry) => entry.timestamp >= startOfToday && entry.timestamp <= endOfToday)
    .map((entry) => ({ x: entry.timestamp, y: entry.power }))
})

const legend = computed(() => {
  void props.theme
  const items = categoryDefs.filter((c) => visibleSeries[c.key]).map((c) => ({ label: c.label, color: getCssColor(c.colorVar) }))
  if (forecastToday.value.length > 1) {
    items.push({ label: 'Prognose', color: getCssColor('--pv') })
  }
  return items
})

// x-axis bounds: the whole day for the day view, or the selected rolling window for live view
const xRange = computed(() => {
  if (mode.value === 'live') {
    return { min: now.value - liveRangeMinutes.value * 60 * 1000, max: now.value }
  }
  return { min: new Date().setHours(0, 0, 0, 0), max: new Date().setHours(23, 59, 59, 999) }
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
          backgroundColor: 'transparent',
          fill: false,
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
        backgroundColor: cat.fill ? hexToRgba(color, 0.18) : 'transparent',
        fill: cat.fill,
        borderWidth: cat.fill ? 2 : 1.25,
        pointRadius: 0,
        tension: 0.2,
      })
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
      borderWidth: 1.5,
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
            return typeof x === 'number' ? formatTooltipTime(x) : ''
          },
        },
      },
      annotation: {
        annotations: {
          now: {
            type: 'line',
            display: mode.value === 'day',
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
        pan: { enabled: true, mode: 'x', onPanComplete: () => (isZoomed.value = true) },
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

.reset-zoom-btn {
  font-size: 12px;
  color: var(--accent);
  background: transparent;
  border: 1px solid var(--border);
  border-radius: 999px;
  padding: 3px 10px;
}

.settings-backdrop {
  position: fixed;
  inset: 0;
  z-index: 10;
}

.settings-panel {
  position: absolute;
  top: calc(100% + 8px);
  left: 0;
  z-index: 11;
  width: 280px;
  max-height: 85vh;
  overflow-y: auto;
  overflow-x: hidden;
  padding: 12px;
  display: flex;
  flex-direction: column;
  gap: 6px;
  box-shadow: 0 8px 24px rgba(0, 0, 0, 0.12);
}

.settings-group-label {
  margin-top: 8px;
}

.settings-group-label:first-child {
  margin-top: 0;
}

.series-toggle {
  display: flex;
  align-items: center;
  gap: 7px;
  font-size: 13px;
  cursor: pointer;
}

.category-block {
  padding: 6px 0;
  border-top: 1px solid var(--border);
}

.category-block:first-of-type {
  border-top: none;
}

.category-mode-row {
  margin: 6px 0 4px 22px;
}

.instance-list {
  display: flex;
  flex-direction: column;
  gap: 4px;
  margin-left: 22px;
}

.instance-toggle {
  font-size: 12px;
  color: var(--muted);
}
</style>
