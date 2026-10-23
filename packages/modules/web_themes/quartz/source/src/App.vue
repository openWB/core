<template>
  <div style="max-width: 1280px; margin: 0 auto; padding: 0 24px 64px">
    <nav
      style="
        display: flex;
        align-items: center;
        justify-content: space-between;
        padding: 20px 0;
        border-bottom: 1px solid var(--border);
        flex-wrap: wrap;
        gap: 16px;
      "
    >
      <a
        href="/openWB/web/"
        style="font-size: 18px; font-weight: 700; letter-spacing: -0.01em; color: var(--text); text-decoration: none"
      >openWB</a>
      <div style="display: flex; align-items: center; gap: 28px">
        <a
          href="/openWB/web/settings/#/Status"
          style="font-size: 14px; font-weight: 500; border-bottom: 2px solid var(--accent); padding: 8px 4px; color: var(--text); text-decoration: none"
        >Status</a>
        <a
          href="/openWB/web/settings/#/Logging/Chart"
          style="font-size: 14px; font-weight: 500; color: var(--muted)"
        >
          Auswertungen
        </a>
        <a
          href="/openWB/web/settings/#/Logging/ChargeLog"
          style="font-size: 14px; font-weight: 500; color: var(--muted)"
        >
          Ladeprotokoll
        </a>
        <a
          href="/openWB/web/settings/"
          style="font-size: 14px; font-weight: 500; color: var(--muted)"
        >Einstellungen</a>
      </div>
      <label style="display: flex; align-items: center; gap: 10px; font-size: 13px; color: var(--muted); cursor: pointer">
        {{ dark ? 'Dunkel' : 'Hell' }}
        <button
          class="theme-switch"
          role="switch"
          :aria-checked="dark"
          :class="{ active: dark }"
          @click="toggleDark"
        >
          <span class="theme-switch-thumb" />
        </button>
      </label>
    </nav>

    <StatusStrip />
    <HistoryChart :theme="theme" />

    <div style="margin-bottom: 16px">
      <BaseTabGroup
        :model-value="activeTab"
        :options="tabs"
        @update="activeTab = $event"
      />
    </div>

    <div
      v-if="showChargePoints"
      class="card-grid"
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

<style scoped>
.theme-switch {
  position: relative;
  width: 44px;
  height: 24px;
  border-radius: 999px;
  border: none;
  padding: 2px;
  display: inline-flex;
  align-items: center;
  background: #d1d5db;
}

.theme-switch.active {
  background: var(--accent);
}

.theme-switch-thumb {
  display: block;
  width: 20px;
  height: 20px;
  border-radius: 999px;
  background: #fff;
  box-shadow: 0 1px 2px rgba(0, 0, 0, 0.3);
  transition: transform 0.15s ease;
}

.theme-switch.active .theme-switch-thumb {
  transform: translateX(20px);
}

.card-grid {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 16px;
  margin-bottom: 24px;
}

@media (max-width: 720px) {
  .card-grid {
    grid-template-columns: 1fr;
  }
}
</style>
