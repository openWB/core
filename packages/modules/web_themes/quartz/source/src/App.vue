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
      <span style="font-size: 18px; font-weight: 700; letter-spacing: -0.01em">openWB</span>
      <div style="display: flex; align-items: center; gap: 28px">
        <span style="font-size: 14px; font-weight: 500; border-bottom: 2px solid var(--accent); padding: 8px 4px">Status</span>
        <a
          href="/openWB/web/settings/#/Logging/ChargeLog"
          style="font-size: 14px; font-weight: 500; color: var(--muted)"
        >
          Auswertungen
        </a>
        <a
          href="/openWB/web/settings/"
          style="font-size: 14px; font-weight: 500; color: var(--muted)"
        >Einstellungen</a>
      </div>
      <label style="display: flex; align-items: center; gap: 10px; font-size: 13px; color: var(--muted); cursor: pointer">
        Dunkel
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
  </div>
</template>

<script setup lang="ts">
import { computed, ref, watchEffect } from 'vue'
import StatusStrip from './components/StatusStrip.vue'
import HistoryChart from './components/HistoryChart.vue'

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
</style>
