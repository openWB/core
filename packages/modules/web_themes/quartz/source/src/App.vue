<template>
  <div class="mx-auto max-w-7xl px-3 pb-16 sm:px-6">
    <nav class="relative flex flex-wrap items-center justify-between gap-4 border-b border-border py-5">
      <a
        href="/openWB/web/"
        class="text-[18px] font-bold tracking-[-0.01em] text-text no-underline"
      >openWB</a>
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

    <template v-if="showChargePoints && (activeTab !== 'alle' || (chargePointIds.length > 0 && visibleSections.has('ladepunkte')))">
      <div
        v-if="activeTab === 'alle'"
        class="settings-group-label mb-2"
      >
        Ladepunkte
      </div>
      <div class="mb-6 grid grid-cols-[repeat(auto-fill,minmax(300px,1fr))] gap-4">
        <ChargePointCard
          v-for="id in chargePointIds"
          :key="id"
          :charge-point-id="id"
        />
      </div>
    </template>

    <template v-if="showVehicles && (activeTab !== 'alle' || (vehicleIds.length > 0 && visibleSections.has('fahrzeuge')))">
      <div
        v-if="activeTab === 'alle'"
        class="settings-group-label mb-2"
      >
        Fahrzeuge
      </div>
      <div class="mb-6 grid grid-cols-[repeat(auto-fill,minmax(300px,1fr))] gap-4">
        <VehicleCard
          v-for="id in vehicleIds"
          :key="id"
          :vehicle-id="id"
        />
      </div>
    </template>

    <template v-if="showBatteries && (activeTab !== 'alle' || (batteryIds.length > 0 && visibleSections.has('speicher')))">
      <div
        v-if="activeTab === 'alle'"
        class="settings-group-label mb-2"
      >
        Speicher
      </div>
      <div class="mb-6 grid grid-cols-[repeat(auto-fill,minmax(300px,1fr))] gap-4">
        <BatteryCard
          v-for="id in batteryIds"
          :key="id"
          :battery-id="id"
        />
      </div>
    </template>

    <template v-if="showCounters && (activeTab !== 'alle' || (counterIds.length > 0 && visibleSections.has('zaehler')))">
      <div
        v-if="activeTab === 'alle'"
        class="settings-group-label mb-2"
      >
        Zähler
      </div>
      <div class="mb-6 grid grid-cols-[repeat(auto-fill,minmax(300px,1fr))] gap-4">
        <CounterCard
          v-for="id in counterIds"
          :key="id"
          :counter-id="id"
        />
      </div>
    </template>

    <template v-if="showInverters && (activeTab !== 'alle' || (inverterIds.length > 0 && visibleSections.has('wechselrichter')))">
      <div
        v-if="activeTab === 'alle'"
        class="settings-group-label mb-2"
      >
        Wechselrichter
      </div>
      <div class="mb-6 grid grid-cols-[repeat(auto-fill,minmax(300px,1fr))] gap-4">
        <InverterCard
          v-for="id in inverterIds"
          :key="id"
          :inverter-id="id"
        />
      </div>
    </template>

    <template v-if="showConsumers && (activeTab !== 'alle' || (consumerIds.length > 0 && visibleSections.has('verbraucher')))">
      <div
        v-if="activeTab === 'alle'"
        class="settings-group-label mb-2"
      >
        Verbraucher
      </div>
      <div class="mb-6 grid grid-cols-[repeat(auto-fill,minmax(300px,1fr))] gap-4">
        <ConsumerCard
          v-for="id in consumerIds"
          :key="id"
          :consumer-id="id"
        />
      </div>
    </template>

    <ThemeSettingsModal
      v-model="showThemeSettings"
      :dark="dark"
      :configured-sections="configuredSections"
      :visible-sections="visibleSections"
      @update:dark="dark = $event"
      @toggle-section="(key, checked) => toggleSection(key as SectionKey, checked)"
    />
  </div>
</template>

<script setup lang="ts">
import { computed, ref, watchEffect } from 'vue'
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
const showChargePoints = computed(() => activeTab.value === 'alle' || activeTab.value === 'ladepunkte')
const showVehicles = computed(() => activeTab.value === 'alle' || activeTab.value === 'fahrzeuge')
const showBatteries = computed(() => activeTab.value === 'alle' || activeTab.value === 'speicher')
const showCounters = computed(() => activeTab.value === 'alle' || activeTab.value === 'zaehler')
const showInverters = computed(() => activeTab.value === 'alle' || activeTab.value === 'wechselrichter')
const showConsumers = computed(() => activeTab.value === 'alle' || activeTab.value === 'verbraucher')

const { chargePointIds } = useChargePoints()
const { vehicleIds } = useVehicles()
const { batteryIds } = useBatteries()
const { counterIds } = useCounters()
const { inverterIds } = useInverters()
const { consumerIds } = useConsumers()

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

const configuredSections = computed(() => {
  const defs: { key: SectionKey; label: string; count: number }[] = [
    { key: 'ladepunkte', label: 'Ladepunkte', count: chargePointIds.value.length },
    { key: 'fahrzeuge', label: 'Fahrzeuge', count: vehicleIds.value.length },
    { key: 'speicher', label: 'Speicher', count: batteryIds.value.length },
    { key: 'zaehler', label: 'Zähler', count: counterIds.value.length },
    { key: 'wechselrichter', label: 'Wechselrichter', count: inverterIds.value.length },
    { key: 'verbraucher', label: 'Verbraucher', count: consumerIds.value.length },
  ]
  return defs.filter((d) => d.count > 0)
})

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
</script>
