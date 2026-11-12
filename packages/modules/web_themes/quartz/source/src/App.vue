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
        :options="tabs"
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

    <ThemeSettingsModal
      v-model="showThemeSettings"
      :dark="dark"
      :show-clock="showClock"
      :configured-sections="configuredSections"
      :visible-sections="visibleSections"
      @update:dark="dark = $event"
      @update:show-clock="showClock = $event"
      @toggle-section="(key, checked) => toggleSection(key as SectionKey, checked)"
    />
  </div>
</template>

<script setup lang="ts">
import { computed, ref, watchEffect, onMounted, onUnmounted, type Component } from 'vue'
import StatusStrip from './components/StatusStrip.vue'
import HistoryChart from './components/HistoryChart.vue'
import ChargePointCard from './components/ChargePointCard.vue'
import VehicleCard from './components/VehicleCard.vue'
import BatteryCard from './components/BatteryCard.vue'
import CounterCard from './components/CounterCard.vue'
import InverterCard from './components/InverterCard.vue'
import ConsumerCard from './components/ConsumerCard.vue'
import BaseTabGroup from './components/BaseTabGroup.vue'
import BaseIconButton from './components/BaseIconButton.vue'
import BasePopover from './components/BasePopover.vue'
import ThemeSettingsModal from './components/ThemeSettingsModal.vue'
import ConnectionIndicator from './components/ConnectionIndicator.vue'
import LoginWidget from './components/LoginWidget.vue'
import IconMenu from './components/icons/IconMenu.vue'
import { useChargePoints } from './composables/useChargePoints'
import { useVehicles } from './composables/useVehicles'
import { useBatteries } from './composables/useBatteries'
import { useCounters } from './composables/useCounters'
import { useInverters } from './composables/useInverters'
import { useConsumers } from './composables/useConsumers'
import { useMqttStore } from './stores/mqtt-store'

const mqttStore = useMqttStore()

type SectionKey = 'ladepunkte' | 'fahrzeuge' | 'speicher' | 'zaehler' | 'wechselrichter' | 'verbraucher'

const tabs = [
  { value: 'alle', label: 'Auswahl' },
  { value: 'ladepunkte', label: 'Ladepunkte' },
  { value: 'fahrzeuge', label: 'Fahrzeuge' },
  { value: 'speicher', label: 'Speicher' },
  { value: 'zaehler', label: 'Zähler' },
  { value: 'wechselrichter', label: 'Wechselrichter' },
  { value: 'verbraucher', label: 'Verbraucher' },
]
const showNavMenu = ref(false)
const activeTab = ref('alle')

const { chargePointIds } = useChargePoints()
const { vehicleIds } = useVehicles()
const { batteryIds } = useBatteries()
const { counterIds } = useCounters()
const { inverterIds } = useInverters()
const { consumerIds } = useConsumers()

interface EntitySection {
  key: SectionKey
  label: string
  component: Component
  ids: number[]
  idProp: string
}

// one entry per entity-type card grid shown on the "Auswahl" overview and its own dedicated tab -
// each grid is otherwise structurally identical, differing only in these 5 fields
const entitySections = computed<EntitySection[]>(() => [
  { key: 'ladepunkte', label: 'Ladepunkte', component: ChargePointCard, ids: chargePointIds.value, idProp: 'chargePointId' },
  { key: 'fahrzeuge', label: 'Fahrzeuge', component: VehicleCard, ids: vehicleIds.value, idProp: 'vehicleId' },
  { key: 'speicher', label: 'Speicher', component: BatteryCard, ids: batteryIds.value, idProp: 'batteryId' },
  { key: 'zaehler', label: 'Zähler', component: CounterCard, ids: counterIds.value, idProp: 'counterId' },
  { key: 'wechselrichter', label: 'Wechselrichter', component: InverterCard, ids: inverterIds.value, idProp: 'inverterId' },
  { key: 'verbraucher', label: 'Verbraucher', component: ConsumerCard, ids: consumerIds.value, idProp: 'consumerId' },
])

// dedicated tab: always show, regardless of card count/visibility settings. "Auswahl": only if
// configured (at least one instance exists) and the user hasn't hidden this section.
function isSectionVisible(section: EntitySection): boolean {
  if (activeTab.value === section.key) return true
  return activeTab.value === 'alle' && section.ids.length > 0 && visibleSections.value.has(section.key)
}

// which entity-type card sections appear in the "Auswahl" overview - the dedicated per-type tabs
// always show their full card grid regardless of this (see v-if conditions above)
const SECTIONS_STORAGE_KEY = 'quartz-visible-sections'
const DEFAULT_VISIBLE_SECTIONS: SectionKey[] = ['ladepunkte', 'fahrzeuge', 'verbraucher']

function loadPersistedSections(): SectionKey[] {
  try {
    const raw = localStorage.getItem(SECTIONS_STORAGE_KEY)
    return raw ? (JSON.parse(raw) as SectionKey[]) : DEFAULT_VISIBLE_SECTIONS
  } catch {
    return DEFAULT_VISIBLE_SECTIONS
  }
}

const visibleSections = ref(new Set<SectionKey>(loadPersistedSections()))
const showThemeSettings = ref(false)

watchEffect(() => {
  try {
    localStorage.setItem(SECTIONS_STORAGE_KEY, JSON.stringify([...visibleSections.value]))
  } catch {
    // ignore storage errors (private browsing etc.)
  }
})

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
const dark = ref(localStorage.getItem(STORAGE_KEY) === 'true')
const theme = computed(() => (dark.value ? 'dark' : 'light'))

// applied to <html>, not a template element, so :root[data-theme] CSS rules actually match
watchEffect(() => {
  document.documentElement.setAttribute('data-theme', theme.value)
})

watchEffect(() => {
  try {
    localStorage.setItem(STORAGE_KEY, String(dark.value))
  } catch {
    // ignore storage errors (private browsing etc.)
  }
})

const CLOCK_STORAGE_KEY = 'quartz-show-clock'
const showClock = ref(localStorage.getItem(CLOCK_STORAGE_KEY) === 'true')
watchEffect(() => {
  try {
    localStorage.setItem(CLOCK_STORAGE_KEY, String(showClock.value))
  } catch {
    // ignore storage errors (private browsing etc.)
  }
})

// minute granularity is enough for a clock display, no need for a per-second tick
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
