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

    <div
      v-if="showChargePoints"
      class="mb-6 grid grid-cols-1 gap-4 min-[721px]:grid-cols-2"
    >
      <ChargePointCard
        v-for="id in chargePointIds"
        :key="id"
        :charge-point-id="id"
      />
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed, ref, watchEffect } from 'vue'
import StatusStrip from './components/StatusStrip.vue'
import HistoryChart from './components/HistoryChart.vue'
import ChargePointCard from './components/ChargePointCard.vue'
import BaseTabGroup from './components/BaseTabGroup.vue'
import { useChargePoints } from './composables/useChargePoints'

const tabs = [
  { value: 'alle', label: 'Alles' },
  { value: 'ladepunkte', label: 'Ladepunkte' },
]
const activeTab = ref('alle')
const showChargePoints = computed(() => activeTab.value === 'alle' || activeTab.value === 'ladepunkte')

const { chargePointIds } = useChargePoints()

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
