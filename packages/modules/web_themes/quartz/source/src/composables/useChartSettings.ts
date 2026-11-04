import { reactive, ref, watchEffect, type Ref } from 'vue'
import type { CategoryData, CategoryKey, SocCategoryData, SocSeries } from '@/types/chart'

export type LegendKey = CategoryKey | 'forecast' | 'batterySoc' | 'vehicleSoc'

export interface CategoryDef {
  key: CategoryKey
  label: string
  colorVar: string
}

export const categoryDefs: CategoryDef[] = [
  { key: 'pv', label: 'Erzeugung', colorVar: '--pv' },
  { key: 'house', label: 'Hausverbrauch', colorVar: '--consumption' },
  { key: 'grid', label: 'Netz', colorVar: '--grid' },
  { key: 'counter', label: 'Zähler', colorVar: '--grid' },
  { key: 'battery', label: 'Speicher', colorVar: '--battery' },
  { key: 'chargepoint', label: 'Ladepunkte', colorVar: '--chargepoint' },
  { key: 'consumer', label: 'Verbraucher', colorVar: '--consumer' },
]

export const viewOptions = [
  { value: 'day', label: 'Heute' },
  { value: 'live', label: 'Live' },
] as const

export const categoryModeOptions = [
  { value: 'combined', label: 'Gesamt' },
  { value: 'individual', label: 'Einzeln' },
] as const

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

function loadPersisted(): PersistedChartSettings {
  try {
    const raw = localStorage.getItem(STORAGE_KEY)
    return raw ? (JSON.parse(raw) as PersistedChartSettings) : {}
  } catch {
    return {}
  }
}

function emptyCategories(): Record<CategoryKey, CategoryData> {
  const empty = { all: [], individual: [] }
  return { pv: empty, house: empty, grid: empty, counter: empty, battery: empty, chargepoint: empty, consumer: empty }
}

/**
 * Shared chart-preference state, now consumed both by HistoryChart.vue (to render) and
 * ThemeSettingsModal.vue (opened from the hamburger menu, a sibling of the chart - the two
 * aren't nested, so this needs to live somewhere both can reach rather than as local component
 * state). A lazily-created singleton (not module-top-level side effects) so the first real call
 * happens from inside a component's setup, after Pinia/the app are already installed - safe
 * since HistoryChart.vue, the only caller that matters for persistence/lifetime, is permanently
 * mounted for the app's whole life (confirmed elsewhere), so there's no premature-unmount risk
 * in tying this to "whichever component calls first" the way there would be for a transient one.
 */
function createChartSettings() {
  const persisted = loadPersisted()

  const mode = ref<'day' | 'live'>(persisted.mode ?? 'day')
  const liveRangeMinutes = ref(persisted.liveRangeMinutes ?? 120)

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

  function isInstanceVisible(category: string, id: string): boolean {
    return instanceVisibility[`${category}:${id}`] ?? true
  }
  function setInstanceVisible(category: string, id: string, visible: boolean): void {
    instanceVisibility[`${category}:${id}`] = visible
  }
  function toggleLegendItem(key: LegendKey): void {
    if (key === 'forecast') forecastVisible.value = !forecastVisible.value
    else if (key === 'batterySoc' || key === 'vehicleSoc') socVisibleSeries[key] = !socVisibleSeries[key]
    else visibleSeries[key] = !visibleSeries[key]
  }

  // live snapshot of the chart's own current category/SoC data, written by HistoryChart.vue
  // (the only component with the real MQTT-sourced data) so the settings modal - a sibling, not
  // a child - can render "which categories/instances exist right now" without independently
  // re-subscribing to the daily-log/live-view feeds itself
  const categories: Ref<Record<CategoryKey, CategoryData>> = ref(emptyCategories())
  const batterySoc: Ref<SocCategoryData> = ref({ all: [], individual: [] })
  const selectedVehicleSoc: Ref<SocSeries[]> = ref([])

  return {
    mode,
    liveRangeMinutes,
    visibleSeries,
    categoryMode,
    instanceVisibility,
    forecastVisible,
    socVisibleSeries,
    socCategoryMode,
    isInstanceVisible,
    setInstanceVisible,
    toggleLegendItem,
    categories,
    batterySoc,
    selectedVehicleSoc,
  }
}

let singleton: ReturnType<typeof createChartSettings> | undefined

export function useChartSettings() {
  if (!singleton) singleton = createChartSettings()
  return singleton
}
