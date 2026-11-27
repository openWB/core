<template>
  <div class="mx-auto max-w-7xl px-3 pb-16 sm:px-6">
    <nav class="relative flex flex-wrap items-center justify-between gap-4 border-b border-border py-5">
      <a
        href="/openWB/web/"
        class="text-[18px] font-bold tracking-[-0.01em] text-text no-underline"
      >openWB</a>
      <span
        v-if="showClock"
        class="pointer-events-none absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 text-[15px] font-semibold text-muted"
      >{{ clockLabel }}</span>
      <div class="flex items-center gap-2">
        <ConnectionIndicator />
        <LoginWidget />
        <BasePopover
          v-model="showNavMenu"
          panel-class="top-[calc(100%_+_8px)] right-0 flex w-56 max-w-[calc(100vw-2rem)] flex-col gap-0.5 p-2"
        >
          <template #trigger="{ toggle }">
            <BaseIconButton
              aria-label="Menü öffnen"
              title="Menü öffnen"
              @click="toggle"
            >
              <IconMenu />
            </BaseIconButton>
          </template>
          <a
            v-if="mqttStore.accessStatusAllowed()"
            href="/openWB/web/settings/#/Status"
            class="rounded-lg px-3 py-2 text-sm font-semibold text-accent no-underline"
            @click="showNavMenu = false"
          >Status</a>
          <a
            v-if="mqttStore.accessChartAllowed()"
            href="/openWB/web/settings/#/Logging/Chart"
            class="rounded-lg px-3 py-2 text-sm font-medium text-text no-underline"
            @click="showNavMenu = false"
          >Auswertungen</a>
          <a
            v-if="mqttStore.accessChargeLogAllowed()"
            href="/openWB/web/settings/#/Logging/ChargeLog"
            class="rounded-lg px-3 py-2 text-sm font-medium text-text no-underline"
            @click="showNavMenu = false"
          >Ladeprotokoll</a>
          <a
            v-if="mqttStore.accessSettingsAllowed()"
            href="/openWB/web/settings/"
            class="rounded-lg px-3 py-2 text-sm font-medium text-text no-underline"
            @click="showNavMenu = false"
          >Einstellungen</a>
          <div class="my-1 border-t border-border" />
          <button
            type="button"
            class="rounded-lg border-0 bg-transparent px-3 py-2 text-left text-sm font-medium text-text"
            @click="showThemeSettings = true; showNavMenu = false"
          >
            Theme-Einstellungen
          </button>
        </BasePopover>
      </div>
    </nav>

    <StatusStrip />
    <HistoryChart :theme="theme" />

    <div class="mb-4 flex flex-wrap items-center justify-between gap-3">
      <BaseTabGroup
        class="min-w-0"
        :model-value="activeTab"
        :options="visibleTabs"
        @update="activeTab = $event"
      />
    </div>

    <template
      v-for="section in entitySections"
      :key="section.key"
    >
      <template v-if="isSectionVisible(section)">
        <div
          v-if="activeTab === 'alle'"
          class="settings-group-label mb-2"
        >
          {{ section.label }}
        </div>
        <div class="mb-6 grid grid-cols-[repeat(auto-fill,minmax(300px,1fr))] gap-4">
          <component
            :is="section.component"
            v-for="id in section.ids"
            :key="id"
            v-bind="{ [section.idProp]: id }"
          />
        </div>
      </template>
    </template>

    <ToastHost />

    <ThemeSettingsModal
      v-model="showThemeSettings"
      :dark="dark"
      :show-clock="showClock"
      :configured-sections="configuredSections"
      :visible-sections="visibleSections"
      @update:dark="setDark"
      @update:show-clock="showClock = $event"
      @toggle-section="(key, checked) => toggleSection(key as SectionKey, checked)"
    />
  </div>
</template>

<script setup lang="ts">
import { computed, ref, watch, watchEffect, onMounted, onUnmounted, type Component } from 'vue'
import StatusStrip from './components/StatusStrip.vue'
import HistoryChart from './components/HistoryChart.vue'
import ChargePointCard from './components/ChargePointCard.vue'
import VehicleCard from './components/VehicleCard.vue'
import BatteryCard from './components/BatteryCard.vue'
import ConsumerCard from './components/ConsumerCard.vue'
import BaseTabGroup from './components/BaseTabGroup.vue'
import BaseIconButton from './components/BaseIconButton.vue'
import BasePopover from './components/BasePopover.vue'
import ThemeSettingsModal from './components/ThemeSettingsModal.vue'
import ConnectionIndicator from './components/ConnectionIndicator.vue'
import ToastHost from './components/ToastHost.vue'
import LoginWidget from './components/LoginWidget.vue'
import IconMenu from './components/icons/IconMenu.vue'
import { useChargePoints } from './composables/useChargePoints'
import { useVehicles } from './composables/useVehicles'
import { useBatteries } from './composables/useBatteries'
import { useConsumers } from './composables/useConsumers'
import { useMqttStore } from './stores/mqtt-store'
import { readStorage, writeStorage } from './utils/storage'

const mqttStore = useMqttStore()

type SectionKey = 'ladepunkte' | 'fahrzeuge' | 'speicher' | 'verbraucher'

const tabs = [
  { value: 'alle', label: 'Auswahl' },
  { value: 'ladepunkte', label: 'Ladepunkte' },
  { value: 'fahrzeuge', label: 'Fahrzeuge' },
  { value: 'speicher', label: 'Speicher' },
  { value: 'verbraucher', label: 'Verbraucher' },
]
const showNavMenu = ref(false)
const activeTab = ref('alle')

const { chargePointIds } = useChargePoints()
const { vehicleIds } = useVehicles()
const { batteryIds } = useBatteries()
const { consumerIds } = useConsumers()

interface EntitySection {
  key: SectionKey
  label: string
  component: Component
  ids: number[]
  idProp: string
}

// one entry per card grid; the grids differ only in these fields
const entitySections = computed<EntitySection[]>(() => [
  { key: 'ladepunkte', label: 'Ladepunkte', component: ChargePointCard, ids: chargePointIds.value, idProp: 'chargePointId' },
  { key: 'fahrzeuge', label: 'Fahrzeuge', component: VehicleCard, ids: vehicleIds.value, idProp: 'vehicleId' },
  { key: 'speicher', label: 'Speicher', component: BatteryCard, ids: batteryIds.value, idProp: 'batteryId' },
  { key: 'verbraucher', label: 'Verbraucher', component: ConsumerCard, ids: consumerIds.value, idProp: 'consumerId' },
])

// a tab for a kind of card the user has none of (or may not see) would only lead to an empty page
const visibleTabs = computed(() =>
  tabs.filter((tab) => tab.value === 'alle' || (entitySections.value.find((s) => s.key === tab.value)?.ids.length ?? 0) > 0),
)
watch(visibleTabs, (list) => {
  if (!list.some((tab) => tab.value === activeTab.value)) activeTab.value = 'alle'
})

// a dedicated tab always shows its grid; "Auswahl" only sections that have cards and are not hidden
function isSectionVisible(section: EntitySection): boolean {
  if (activeTab.value === section.key) return true
  return activeTab.value === 'alle' && section.ids.length > 0 && visibleSections.value.has(section.key)
}

// which card sections "Auswahl" shows
const SECTIONS_STORAGE_KEY = 'quartz-visible-sections'
const ALL_SECTION_KEYS: SectionKey[] = ['ladepunkte', 'fahrzeuge', 'speicher', 'verbraucher']
const DEFAULT_VISIBLE_SECTIONS: SectionKey[] = ['ladepunkte', 'fahrzeuge', 'verbraucher']

function loadPersistedSections(): SectionKey[] {
  try {
    const raw = readStorage(SECTIONS_STORAGE_KEY)
    // drop sections that no longer exist
    return raw ? (JSON.parse(raw) as SectionKey[]).filter((key) => ALL_SECTION_KEYS.includes(key)) : DEFAULT_VISIBLE_SECTIONS
  } catch {
    return DEFAULT_VISIBLE_SECTIONS
  }
}

const visibleSections = ref(new Set<SectionKey>(loadPersistedSections()))
const showThemeSettings = ref(false)

watchEffect(() => writeStorage(SECTIONS_STORAGE_KEY, JSON.stringify([...visibleSections.value])))

function toggleSection(key: SectionKey, checked: boolean): void {
  if (checked) visibleSections.value.add(key)
  else visibleSections.value.delete(key)
  visibleSections.value = new Set(visibleSections.value)
}

const configuredSections = computed(() =>
  entitySections.value
    .filter((s) => s.ids.length > 0)
    .map((s) => ({ key: s.key, label: s.label, count: s.ids.length })),
)

const STORAGE_KEY = 'quartz-dark-mode'
// follows the system until the user chooses; stored only when chosen
const storedDark = readStorage(STORAGE_KEY)
const prefersDark = typeof window.matchMedia === 'function' && window.matchMedia('(prefers-color-scheme: dark)').matches
const dark = ref(storedDark === null ? prefersDark : storedDark === 'true')
function setDark(value: boolean): void {
  dark.value = value
  writeStorage(STORAGE_KEY, String(value))
}
const theme = computed(() => (dark.value ? 'dark' : 'light'))

// on <html>, so :root[data-theme] rules match
watchEffect(() => {
  document.documentElement.setAttribute('data-theme', theme.value)
})

const CLOCK_STORAGE_KEY = 'quartz-show-clock'
const showClock = ref(readStorage(CLOCK_STORAGE_KEY) === 'true')
watchEffect(() => writeStorage(CLOCK_STORAGE_KEY, String(showClock.value)))

const now = ref(new Date())
let clockTimer: ReturnType<typeof setInterval> | undefined
onMounted(() => {
  clockTimer = setInterval(() => {
    now.value = new Date()
  }, 20_000)
})
onUnmounted(() => clearInterval(clockTimer))
const clockLabel = computed(() => now.value.toLocaleTimeString('de-DE', { hour: '2-digit', minute: '2-digit' }))
</script>
