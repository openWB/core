import { reactive, ref, watchEffect, type Ref } from 'vue'
import { readStorage, writeStorage } from '@/utils/storage'
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
const categoryKeys = categoryDefs.map((c) => c.key)

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
  showFlow?: boolean
  showChart?: boolean
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
    const raw = readStorage(STORAGE_KEY)
    return raw ? (JSON.parse(raw) as PersistedChartSettings) : {}
  } catch {
    return {}
  }
}

function emptyCategories(): Record<CategoryKey, CategoryData> {
  const empty = { all: [], individual: [] }
  return Object.fromEntries(categoryKeys.map((key) => [key, empty])) as unknown as Record<CategoryKey, CategoryData>
}

/** Chart preferences shared by HistoryChart and ThemeSettingsModal, which are not nested. Created lazily so the first call happens inside a component's setup, after Pinia exists. */
function createChartSettings() {
  const persisted = loadPersisted()

  const mode = ref<'day' | 'live'>(persisted.mode ?? 'day')
  const liveRangeMinutes = ref(persisted.liveRangeMinutes ?? 120)
  const showFlow = ref(persisted.showFlow ?? true)
  const showChart = ref(persisted.showChart ?? true)

  const visibleSeries = reactive<Record<CategoryKey, boolean>>({
    ...(Object.fromEntries(categoryKeys.map((key) => [key, true])) as Record<CategoryKey, boolean>),
    ...persisted.visibleSeries,
  })

  // "Einzeln" by default for categories that usually have several instances
  const INDIVIDUAL_BY_DEFAULT: CategoryKey[] = ['chargepoint', 'consumer', 'counter']
  const categoryMode = reactive<Record<CategoryKey, 'combined' | 'individual'>>({
    ...(Object.fromEntries(
      categoryKeys.map((key) => [key, INDIVIDUAL_BY_DEFAULT.includes(key) ? 'individual' : 'combined']),
    ) as Record<CategoryKey, 'combined' | 'individual'>),
    ...persisted.categoryMode,
  })

  // keyed "<category>:<instanceId>"; new components are visible by default
  const instanceVisibility = reactive<Record<string, boolean>>({ ...persisted.instanceVisibility })

  // independent of the Erzeugung line: hiding one should not hide the other
  const forecastVisible = ref(persisted.forecastVisible ?? true)

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
      showFlow: showFlow.value,
      showChart: showChart.value,
      liveRangeMinutes: liveRangeMinutes.value,
      visibleSeries: { ...visibleSeries },
      categoryMode: { ...categoryMode },
      instanceVisibility: { ...instanceVisibility },
      forecastVisible: forecastVisible.value,
      socVisibleSeries: { ...socVisibleSeries },
      socCategoryMode: { ...socCategoryMode },
    }
    writeStorage(STORAGE_KEY, JSON.stringify(settings))
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

  // snapshot of the chart's data, written by HistoryChart for the settings modal
  const categories: Ref<Record<CategoryKey, CategoryData>> = ref(emptyCategories())
  const batterySoc: Ref<SocCategoryData> = ref({ all: [], individual: [] })
  const selectedVehicleSoc: Ref<SocSeries[]> = ref([])

  return {
    mode,
    showFlow,
    showChart,
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
