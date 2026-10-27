<template>
  <div class="mx-auto max-w-7xl px-6 pb-16">
    <nav class="flex flex-wrap items-center justify-between gap-4 border-b border-border py-5">
      <a
        href="/openWB/web/"
        class="text-[18px] font-bold tracking-[-0.01em] text-text no-underline"
      >openWB</a>
      <div class="flex items-center gap-7">
        <a
          href="/openWB/web/settings/#/Status"
          class="border-b-2 border-accent px-1 py-2 text-sm font-medium text-text no-underline"
        >Status</a>
        <a
          href="/openWB/web/settings/#/Logging/Chart"
          class="text-sm font-medium text-muted"
        >
          Auswertungen
        </a>
        <a
          href="/openWB/web/settings/#/Logging/ChargeLog"
          class="text-sm font-medium text-muted"
        >
          Ladeprotokoll
        </a>
        <a
          href="/openWB/web/settings/"
          class="text-sm font-medium text-muted"
        >Einstellungen</a>
      </div>
      <label class="flex cursor-pointer items-center gap-2.5 text-[13px] text-muted">
        {{ dark ? 'Dunkel' : 'Hell' }}
        <button
          class="relative inline-flex h-6 w-11 items-center rounded-full border-0 bg-[#d1d5db] p-0.5"
          role="switch"
          :aria-checked="dark"
          :class="{ 'bg-accent': dark }"
          @click="toggleDark"
        >
          <span
            class="block h-5 w-5 rounded-full bg-white shadow-[0_1px_2px_rgba(0,0,0,0.3)] transition-transform duration-150 [transition-timing-function:ease]"
            :class="{ 'translate-x-5': dark }"
          />
        </button>
      </label>
    </nav>

    <StatusStrip />
    <HistoryChart :theme="theme" />

    <div class="mb-4">
      <BaseTabGroup
        :model-value="activeTab"
        :options="tabs"
        @update="activeTab = $event"
      />
    </div>

    <template v-if="showChargePoints && (activeTab !== 'alle' || chargePointIds.length > 0)">
      <div
        v-if="activeTab === 'alle'"
        class="settings-group-label mb-2"
      >
        Ladepunkte
      </div>
      <div class="mb-6 grid grid-cols-[repeat(auto-fit,minmax(300px,1fr))] gap-4">
        <ChargePointCard
          v-for="id in chargePointIds"
          :key="id"
          :charge-point-id="id"
        />
      </div>
    </template>

    <template v-if="showVehicles && (activeTab !== 'alle' || vehicleIds.length > 0)">
      <div
        v-if="activeTab === 'alle'"
        class="settings-group-label mb-2"
      >
        Fahrzeuge
      </div>
      <div class="mb-6 grid grid-cols-[repeat(auto-fit,minmax(300px,1fr))] gap-4">
        <VehicleCard
          v-for="id in vehicleIds"
          :key="id"
          :vehicle-id="id"
        />
      </div>
    </template>

    <template v-if="showBatteries && (activeTab !== 'alle' || batteryIds.length > 0)">
      <div
        v-if="activeTab === 'alle'"
        class="settings-group-label mb-2"
      >
        Speicher
      </div>
      <div class="mb-6 grid grid-cols-[repeat(auto-fit,minmax(300px,1fr))] gap-4">
        <BatteryCard
          v-for="id in batteryIds"
          :key="id"
          :battery-id="id"
        />
      </div>
    </template>

    <template v-if="showCounters && (activeTab !== 'alle' || counterIds.length > 0)">
      <div
        v-if="activeTab === 'alle'"
        class="settings-group-label mb-2"
      >
        Zähler
      </div>
      <div class="mb-6 grid grid-cols-[repeat(auto-fit,minmax(300px,1fr))] gap-4">
        <CounterCard
          v-for="id in counterIds"
          :key="id"
          :counter-id="id"
        />
      </div>
    </template>

    <template v-if="showInverters && (activeTab !== 'alle' || inverterIds.length > 0)">
      <div
        v-if="activeTab === 'alle'"
        class="settings-group-label mb-2"
      >
        Wechselrichter
      </div>
      <div class="mb-6 grid grid-cols-[repeat(auto-fit,minmax(300px,1fr))] gap-4">
        <InverterCard
          v-for="id in inverterIds"
          :key="id"
          :inverter-id="id"
        />
      </div>
    </template>

    <template v-if="showConsumers && (activeTab !== 'alle' || consumerIds.length > 0)">
      <div
        v-if="activeTab === 'alle'"
        class="settings-group-label mb-2"
      >
        Verbraucher
      </div>
      <div class="mb-6 grid grid-cols-[repeat(auto-fit,minmax(300px,1fr))] gap-4">
        <ConsumerCard
          v-for="id in consumerIds"
          :key="id"
          :consumer-id="id"
        />
      </div>
    </template>
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
import { useChargePoints } from './composables/useChargePoints'
import { useVehicles } from './composables/useVehicles'
import { useBatteries } from './composables/useBatteries'
import { useCounters } from './composables/useCounters'
import { useInverters } from './composables/useInverters'
import { useConsumers } from './composables/useConsumers'

const tabs = [
  { value: 'alle', label: 'Alles' },
  { value: 'ladepunkte', label: 'Ladepunkte' },
  { value: 'fahrzeuge', label: 'Fahrzeuge' },
  { value: 'speicher', label: 'Speicher' },
  { value: 'zaehler', label: 'Zähler' },
  { value: 'wechselrichter', label: 'Wechselrichter' },
  { value: 'verbraucher', label: 'Verbraucher' },
]
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

const STORAGE_KEY = 'quartz-dark-mode'
const dark = ref(localStorage.getItem(STORAGE_KEY) === 'true')
const theme = computed(() => (dark.value ? 'dark' : 'light'))

// applied to <html>, not a template element, so :root[data-theme] CSS rules actually match
watchEffect(() => {
  document.documentElement.setAttribute('data-theme', theme.value)
})

function toggleDark(): void {
  dark.value = !dark.value
  try {
    localStorage.setItem(STORAGE_KEY, String(dark.value))
  } catch {
    // ignore storage errors (private browsing etc.)
  }
}
</script>
