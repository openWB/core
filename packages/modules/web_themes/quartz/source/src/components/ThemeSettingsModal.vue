<template>
  <BaseModal
    :model-value="modelValue"
    title="Theme-Einstellungen"
    :width="880"
    @update:model-value="$emit('update:modelValue', $event)"
  >
    <div class="rounded-lg bg-bg p-3">
      <div class="settings-group-label mb-2">
        Darstellung
      </div>

      <label class="mb-2 block text-[13px] text-muted">Fluss anzeigen</label>
      <BaseToggle
        :model-value="showFlow"
        @update:model-value="showFlow = $event"
      />

      <label class="mt-3 mb-2 block text-[13px] text-muted">Verlauf anzeigen</label>
      <BaseToggle
        :model-value="showChart"
        @update:model-value="showChart = $event"
      />

      <DarkModeToggle
        class="mt-3"
        :model-value="dark"
        @update:model-value="$emit('update:dark', $event)"
      />

      <div class="mt-3">
        <label class="mb-2 block text-[13px] text-muted">Uhrzeit anzeigen</label>
        <BaseToggle
          :model-value="showClock"
          @update:model-value="$emit('update:showClock', $event)"
        />
      </div>

      <div class="mt-3">
        <label class="mb-2 block text-[13px] text-muted">Standard-Fahrzeug anzeigen</label>
        <BaseToggle
          :model-value="!hideStandardVehicle"
          @update:model-value="hideStandardVehicle = !$event"
        />
      </div>
    </div>

    <div
      v-if="configuredSections.length > 0"
      class="mt-3 rounded-lg bg-bg p-3"
    >
      <div class="settings-group-label mb-2">
        Kartenanzeige
      </div>
      <div class="mode-note mt-0 mb-2">
        Karten unter "Auswahl" anzeigen
      </div>
      <div class="grid grid-cols-2 gap-x-4 sm:grid-cols-3">
        <label
          v-for="section in configuredSections"
          :key="section.key"
          class="flex cursor-pointer items-center gap-2 rounded-lg px-1 py-2 text-sm text-text"
        >
          <input
            type="checkbox"
            :checked="visibleSections.has(section.key)"
            @change="$emit('toggle-section', section.key, ($event.target as HTMLInputElement).checked)"
          >
          {{ section.label }}
        </label>
      </div>
    </div>

    <div class="mt-3 rounded-lg bg-bg p-3">
      <div class="settings-group-label mb-2">
        Diagramm
      </div>

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
        <div class="settings-group-label mt-2">
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
          powerColumnCategories.length > 0 ||
            usageColumnCategories.length > 0 ||
            batterySoc.individual.length > 0 ||
            selectedVehicleSoc.length > 1
        "
      >
        <div class="settings-group-label mt-2">
          Linien
        </div>
        <div class="sm:grid sm:grid-cols-3 sm:gap-x-6">
          <CategoryLinesColumn :category-defs="powerColumnCategories" />
          <CategoryLinesColumn :category-defs="usageColumnCategories" />

          <div>
            <LineGroup
              v-if="batterySoc.individual.length > 0"
              label="Speicher-SoC"
              :color="getCssColor('--battery')"
              :mode="socCategoryMode.batterySoc"
              :items="batterySoc.individual"
              :is-visible="(id) => isInstanceVisible('batterySoc', id)"
              :set-visible="(id, visible) => setInstanceVisible('batterySoc', id, visible)"
              @update:mode="socCategoryMode.batterySoc = $event"
            />

            <LineGroup
              v-if="selectedVehicleSoc.length > 1"
              label="Fahrzeug-SoC"
              :color="getCssColor('--car')"
              :items="selectedVehicleSoc"
              :is-visible="(id) => isInstanceVisible('vehicleSoc', id)"
              :set-visible="(id, visible) => setInstanceVisible('vehicleSoc', id, visible)"
            />
          </div>
        </div>
      </template>
    </div>
  </BaseModal>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import { useMqttStore } from '@/stores/mqtt-store'
import { useChartSettings, categoryDefs, viewOptions } from '@/composables/useChartSettings'
import { useVehicles } from '@/composables/useVehicles'
import { getCssColor } from '@/utils/color'
import type { CategoryKey } from '@/types/chart'
import BaseModal from './BaseModal.vue'
import BaseTabGroup from './BaseTabGroup.vue'
import DarkModeToggle from './DarkModeToggle.vue'
import BaseToggle from './BaseToggle.vue'
import CategoryLinesColumn from './CategoryLinesColumn.vue'
import LineGroup from './LineGroup.vue'

defineProps<{
  modelValue: boolean
  dark: boolean
  showClock: boolean
  configuredSections: { key: string; label: string }[]
  visibleSections: Set<string>
}>()
defineEmits<{
  'update:modelValue': [value: boolean]
  'update:dark': [value: boolean]
  'update:showClock': [value: boolean]
  'toggle-section': [key: string, checked: boolean]
}>()

const mqttStore = useMqttStore()
const {
  mode,
  showFlow,
  showChart,
  liveRangeMinutes,
  socCategoryMode,
  isInstanceVisible,
  setInstanceVisible,
  categories,
  batterySoc,
  selectedVehicleSoc,
} = useChartSettings()
const { hideStandardVehicle } = useVehicles()

// mirrors HistoryChart.vue's own categoryHasComponent/visibleCategoryDefs - re-derived here
// from the same published 'categories' snapshot rather than duplicated as more published refs,
// since it's only a couple of lines and both places already need mqttStore + categoryDefs anyway
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

// only categories that actually offer a real Gesamt/Einzeln choice belong here - pv/battery
// never have per-instance breakdown in Live mode (the live feed only ever publishes aggregates
// there, unlike the daily log), so a switcher with nothing to switch to would be pointless; they
// simply don't appear in Live's "Linien" list, same as before this round's UI pass (confirmed
// with the user this is the right call once they understood why, not something to paper over)
const categoriesWithIndividualBreakdown = computed(() =>
  visibleCategoryDefs.value.filter((c) => categories.value[c.key].individual.length > 0),
)

// explicit 3-lane grouping for the "Linien" grid (power-generation/storage, usage, SoC lines) -
// the user asked for this specific grouping rather than an auto-balanced column flow
const POWER_COLUMN_KEYS: CategoryKey[] = ['pv', 'counter', 'battery']
const USAGE_COLUMN_KEYS: CategoryKey[] = ['consumer', 'chargepoint']
const powerColumnCategories = computed(() =>
  categoriesWithIndividualBreakdown.value.filter((c) => POWER_COLUMN_KEYS.includes(c.key)),
)
const usageColumnCategories = computed(() =>
  categoriesWithIndividualBreakdown.value.filter((c) => USAGE_COLUMN_KEYS.includes(c.key)),
)
</script>
