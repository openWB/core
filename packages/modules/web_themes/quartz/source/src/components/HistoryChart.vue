<template>
  <div class="panel relative mb-6 px-3 pt-5 pb-4 sm:px-6">
    <div class="mb-3 flex flex-wrap items-center justify-between gap-3">
      <div class="flex items-center gap-2">
        <h2 class="m-0 flex items-center gap-2 text-base font-bold">
          Verlauf ·
          <button
            type="button"
            class="cursor-pointer rounded-full border-0 px-2.5 py-1 text-[13px] font-semibold badge-muted"
            @click="mode = mode === 'day' ? 'live' : 'day'"
          >
            {{ mode === 'day' ? 'Heute' : `Live · ${liveRangeMinutes} Min` }}
          </button>
        </h2>
        <div class="sm:relative">
          <BaseIconButton
            aria-label="Diagramm-Einstellungen"
            @click="showSettings = !showSettings"
          >
            <IconGear />
          </BaseIconButton>
          <div
            v-if="showSettings"
            class="fixed inset-0 z-10"
            @click="showSettings = false"
          />
          <div
            v-if="showSettings"
            class="panel absolute top-14 right-3 left-3 z-[11] flex max-h-[85vh] flex-col gap-1.5 overflow-y-auto overflow-x-hidden p-3 shadow-[0_8px_24px_rgba(0,0,0,0.12)] sm:top-[calc(100%_+_8px)] sm:right-auto sm:left-0 sm:w-70"
          >
            <div class="settings-group-label mt-2 first:mt-0">
              Ansicht
            </div>
            <BaseTabGroup
              dense
              :model-value="mode"
              :options="viewOptions"
              @update="mode = $event"
            />

            <template v-if="mode === 'live'">
              <div class="settings-group-label mt-2 first:mt-0">
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

            <template
              v-if="
                categoriesWithIndividualBreakdown.length > 0 || batterySoc.individual.length > 0 || selectedVehicleSoc.length > 1
              "
            >
              <div class="settings-group-label mt-2 first:mt-0">
                Linien
              </div>
              <div
                v-for="cat in categoriesWithIndividualBreakdown"
                :key="cat.key"
                class="border-t border-border py-1.5 first-of-type:border-t-0"
              >
                <div class="flex items-center gap-[7px] text-[13px]">
                  <span
                    class="legend-dot"
                    :style="{ background: getCssColor(cat.colorVar) }"
                  />
                  {{ cat.label }}
                </div>

                <div class="mt-1.5 mb-1">
                  <BaseTabGroup
                    dense
                    :model-value="categoryMode[cat.key]"
                    :options="categoryModeOptions"
                    @update="categoryMode[cat.key] = $event"
                  />
                </div>

                <div
                  v-if="categoryMode[cat.key] === 'individual'"
                  class="flex flex-col gap-1"
                >
                  <label
                    v-for="(inst, idx) in categories[cat.key].individual"
                    :key="inst.id"
                    class="flex cursor-pointer items-center gap-[7px] text-xs text-muted"
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

              <div
                v-if="batterySoc.individual.length > 0"
                class="border-t border-border py-1.5"
              >
                <div class="flex items-center gap-[7px] text-[13px]">
                  <span
                    class="legend-dot"
                    :style="{ background: getCssColor('--battery') }"
                  />
                  Speicher-SoC
                </div>

                <div class="mt-1.5 mb-1">
                  <BaseTabGroup
                    dense
                    :model-value="socCategoryMode.batterySoc"
                    :options="categoryModeOptions"
                    @update="socCategoryMode.batterySoc = $event"
                  />
                </div>

                <div
                  v-if="socCategoryMode.batterySoc === 'individual'"
                  class="flex flex-col gap-1"
                >
                  <label
                    v-for="(inst, idx) in batterySoc.individual"
                    :key="inst.id"
                    class="flex cursor-pointer items-center gap-[7px] text-xs text-muted"
                  >
                    <input
                      type="checkbox"
                      :checked="isInstanceVisible('batterySoc', inst.id)"
                      @change="setInstanceVisible('batterySoc', inst.id, ($event.target as HTMLInputElement).checked)"
                    >
                    <span
                      class="legend-dot"
                      :style="{ background: instanceColor(getCssColor('--battery'), idx) }"
                    />
                    {{ inst.label }}
                  </label>
                </div>
              </div>

              <div
                v-if="selectedVehicleSoc.length > 1"
                class="border-t border-border py-1.5"
              >
                <div class="flex items-center gap-[7px] text-[13px]">
                  <span
                    class="legend-dot"
                    :style="{ background: getCssColor('--car') }"
                  />
                  Fahrzeug-SoC
                </div>
                <div class="mt-1.5 flex flex-col gap-1">
                  <label
                    v-for="(veh, idx) in selectedVehicleSoc"
                    :key="veh.id"
                    class="flex cursor-pointer items-center gap-[7px] text-xs text-muted"
                  >
                    <input
                      type="checkbox"
                      :checked="isInstanceVisible('vehicleSoc', veh.id)"
                      @change="setInstanceVisible('vehicleSoc', veh.id, ($event.target as HTMLInputElement).checked)"
                    >
                    <span
                      class="legend-dot"
                      :style="{ background: instanceColor(getCssColor('--car'), idx) }"
                    />
                    {{ veh.label }}
                  </label>
                </div>
              </div>
            </template>
          </div>
        </div>
      </div>
      <div class="scrollbar-hide flex flex-nowrap items-center gap-4 overflow-x-auto sm:flex-wrap sm:overflow-visible">
        <button
          v-for="item in legend"
          :key="item.key"
          type="button"
          class="flex flex-none cursor-pointer items-center gap-1.5 border-0 bg-transparent p-0 text-xs whitespace-nowrap text-muted"
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
  forecastVisible?: boolean
  socVisibleSeries?: Partial<Record<'batterySoc' | 'vehicleSoc', boolean>>
  socCategoryMode?: Partial<Record<'batterySoc', 'combined' | 'individual'>>
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

const { categories: dayCategories, batterySoc: dayBatterySoc, vehicleSocAll: dayVehicleSocAll } = useDailyLog()
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
}

const categoryDefs: CategoryDef[] = [
  { key: 'pv', label: 'Erzeugung', colorVar: '--pv' },
  { key: 'house', label: 'Hausverbrauch', colorVar: '--consumption' },
  { key: 'grid', label: 'Netz', colorVar: '--grid' },
  { key: 'counter', label: 'Zähler', colorVar: '--grid' },
  { key: 'battery', label: 'Speicher', colorVar: '--battery' },
  { key: 'chargepoint', label: 'Ladepunkte', colorVar: '--chargepoint' },
  { key: 'consumer', label: 'Verbraucher', colorVar: '--consumer' },
]

const visibleSeries = reactive<Record<CategoryKey, boolean>>({
  pv: true,
  house: true,
  grid: true,
  counter: true,
  battery: true,
  chargepoint: true,
  consumer: true,
  ...persisted.visibleSeries,
})

const categoryMode = reactive<Record<CategoryKey, 'combined' | 'individual'>>({
  pv: 'combined',
  house: 'combined',
  grid: 'combined',
  counter: 'combined',
  battery: 'combined',
  chargepoint: 'combined',
  consumer: 'combined',
  ...persisted.categoryMode,
})

// per-instance visibility within "Einzeln" mode, keyed "<category>:<instanceId>" - defaults to
// visible so a newly-appeared component shows up without the user having to opt it in
const instanceVisibility = reactive<Record<string, boolean>>({ ...persisted.instanceVisibility })

// independent of visibleSeries.pv on purpose - hiding the real Erzeugung line shouldn't also
// hide the forecast (and vice versa), they're separate things a user may want toggled separately
const forecastVisible = ref(persisted.forecastVisible ?? true)

// overall show/hide per SoC line, same role visibleSeries plays for the power categories -
// per-instance (which battery, which vehicle) is handled by instanceVisibility below instead,
// same split power categories already use between "show this category" and "show this instance"
const socVisibleSeries = reactive<Record<'batterySoc' | 'vehicleSoc', boolean>>({
  batterySoc: true,
  vehicleSoc: true,
  ...persisted.socVisibleSeries,
})
const socCategoryMode = reactive<Record<'batterySoc', 'combined' | 'individual'>>({
  batterySoc: 'combined',
  ...persisted.socCategoryMode,
})

watchEffect(() => {
  const settings: PersistedChartSettings = {
    mode: mode.value,
    liveRangeMinutes: liveRangeMinutes.value,
    visibleSeries: { ...visibleSeries },
    categoryMode: { ...categoryMode },
    instanceVisibility: { ...instanceVisibility },
    forecastVisible: forecastVisible.value,
    socVisibleSeries: { ...socVisibleSeries },
    socCategoryMode: { ...socCategoryMode },
  }
  try {
    localStorage.setItem(STORAGE_KEY, JSON.stringify(settings))
  } catch {
    // ignore storage errors (private browsing etc.)
  }
})

// category is CategoryKey for the power categories, or 'batterySoc'/'vehicleSoc' for the SoC
// lines - instanceVisibility itself is just a generic string-keyed map, so both share it
function isInstanceVisible(category: string, id: string): boolean {
  return instanceVisibility[`${category}:${id}`] ?? true
}
function setInstanceVisible(category: string, id: string, visible: boolean): void {
  instanceVisibility[`${category}:${id}`] = visible
}

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

// whole-day forecast, independent of how much real history exists - history can be
// flat/missing (component in error state, or just started) while the forecast for
// today is already known in full; only meaningful next to the day view's combined PV line.
// Split from forecastToday (the actually-drawn series) so the legend item can stay present and
// clickable even while forecastVisible is off - otherwise toggling it hides the only way back on.
const forecastSeriesToday = computed(() => {
  if (mode.value !== 'day' || categoryMode.pv !== 'combined' || !mqttStore.forecastConfigured) {
    return []
  }
  const startOfToday = new Date().setHours(0, 0, 0, 0)
  const endOfToday = new Date().setHours(23, 59, 59, 999)
  const raw = mqttStore.forecastSeries
    .filter((entry) => entry.timestamp >= startOfToday && entry.timestamp <= endOfToday)
    .map((entry) => ({ x: entry.timestamp, y: entry.power }))
  // only resample the elapsed portion (where real power data exists and needs shared-index
  // tooltip alignment) - grid.all has no entries for the future, so resampling the whole series
  // onto it would silently cut the forecast off at "now" instead of showing the rest of the day.
  // grid.all also doesn't necessarily start at 00:00 (e.g. a system only switched on at 13:00
  // today has no log entries before that) - any forecast points before its first timestamp need
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
const forecastToday = computed(() => (forecastVisible.value ? forecastSeriesToday.value : []))

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

// only categories that actually offer a Gesamt/Einzeln choice belong in the settings panel -
// per-category show/hide itself now lives in the clickable legend, not duplicated here
const categoriesWithIndividualBreakdown = computed(() =>
  visibleCategoryDefs.value.filter((c) => categories.value[c.key].individual.length > 0),
)

type LegendKey = CategoryKey | 'forecast' | 'batterySoc' | 'vehicleSoc'

const legend = computed(() => {
  void props.theme
  const items = visibleCategoryDefs.value.map((c) => ({
    key: c.key as LegendKey,
    label: c.label,
    color: getCssColor(c.colorVar),
    visible: visibleSeries[c.key],
  }))
  if (forecastSeriesToday.value.length > 1) {
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

function toggleLegendItem(key: LegendKey): void {
  if (key === 'forecast') forecastVisible.value = !forecastVisible.value
  else if (key === 'batterySoc' || key === 'vehicleSoc') socVisibleSeries[key] = !socVisibleSeries[key]
  else visibleSeries[key] = !visibleSeries[key]
}

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
