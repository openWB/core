<template>
  <div>
    <template v-if="!editing">
      <span class="field-label">Zeitfenster</span>
      <p
        v-if="plans.length === 0"
        class="mode-note"
      >
        Keine Zeitfenster konfiguriert.
      </p>
      <div
        v-for="(plan, index) in plans"
        :key="plan.id ?? index"
        class="plan-row"
        @click="openEdit(plan, index)"
      >
        <span>
          {{ plan.name }} &middot; {{ plan.time[0] }}&ndash;{{ plan.time[1] }} Uhr
          <span
            v-if="!plan.active"
            class="plan-inactive"
          >(inaktiv)</span>
        </span>
        <span class="plan-frequency">{{ frequencyLabel(plan.frequency.selected) }}</span>
      </div>
      <button
        type="button"
        class="add-plan-btn"
        @click="openNew"
      >
        + Neues Zeitfenster
      </button>
    </template>

    <template v-else>
      <div class="plan-edit-head">
        <BaseButton @click="editing = null">
          &larr; Zurück
        </BaseButton>
        <BaseButton
          v-if="editingIndex !== null"
          variant="danger"
          @click="remove"
        >
          Löschen
        </BaseButton>
      </div>

      <label
        class="field-label"
        for="tp-name"
      >Name</label>
      <input
        id="tp-name"
        v-model="editing.name"
        type="text"
        class="field-select"
      >

      <div class="toggle-row">
        <label for="tp-active">Aktiv</label>
        <input
          id="tp-active"
          v-model="editing.active"
          type="checkbox"
        >
      </div>

      <span class="field-label">Zeitraum</span>
      <div class="time-range-row">
        <input
          v-model="editing.time[0]"
          type="time"
          class="field-select"
        >
        <span>bis</span>
        <input
          v-model="editing.time[1]"
          type="time"
          class="field-select"
        >
      </div>

      <BaseSegmentedControl
        label="Häufigkeit"
        :model-value="editing.frequency.selected"
        :options="frequencyOptions"
        @update="editing.frequency.selected = $event"
      />
      <WeekdayToggle
        v-if="editing.frequency.selected === 'weekly'"
        :model-value="editing.frequency.weekly"
        @update="(v) => (editing!.frequency.weekly = v)"
      />
      <div
        v-if="editing.frequency.selected === 'once'"
        class="time-range-row"
      >
        <input
          v-model="editing.frequency.once[0]"
          type="date"
          class="field-select"
        >
        <span>bis</span>
        <input
          v-model="editing.frequency.once[1]"
          type="date"
          class="field-select"
        >
      </div>

      <FieldSlider
        label="Ladestrom"
        unit="A"
        :min="6"
        :max="32"
        :model-value="editing.current"
        @update="(v) => (editing!.current = v)"
      />
      <BaseSegmentedControl
        :model-value="editing.phases_to_use"
        :options="[{ value: 1, label: '1' }, { value: 3, label: 'Maximum' }]"
        @update="(v) => (editing!.phases_to_use = v)"
      />

      <BaseSegmentedControl
        label="Begrenzung"
        :model-value="editing.limit.selected"
        :options="limitOptions"
        @update="editing.limit.selected = $event"
      />
      <FieldSlider
        v-if="editing.limit.selected === 'soc'"
        label="Ziel-SoC"
        unit="%"
        :min="0"
        :max="100"
        :model-value="editing.limit.soc"
        @update="(v) => (editing!.limit.soc = v)"
      />
      <FieldSlider
        v-if="editing.limit.selected === 'amount'"
        label="Energiemenge"
        unit="kWh"
        :min="0"
        :max="100"
        :decimals="1"
        :model-value="editing.limit.amount / 1000"
        @update="(v) => (editing!.limit.amount = v * 1000)"
      />

      <div class="toggle-row">
        <label for="tp-bat">Nur wenn Speicher-SoC erreicht</label>
        <input
          id="tp-bat"
          type="checkbox"
          :checked="editing.min_bat_soc !== null"
          @change="toggleMinBatSoc(($event.target as HTMLInputElement).checked)"
        >
      </div>
      <FieldSlider
        v-if="editing.min_bat_soc !== null"
        label="Mindest-Speicher-SoC"
        unit="%"
        :min="0"
        :max="100"
        :model-value="editing.min_bat_soc"
        @update="(v) => (editing!.min_bat_soc = v)"
      />

      <BaseButton
        variant="primary"
        style="width: 100%; margin-top: 14px"
        @click="save"
      >
        Speichern
      </BaseButton>
    </template>
  </div>
</template>

<script setup lang="ts">
import { computed, ref } from 'vue'
import { useMqttStore, type TimeChargingPlan } from '@/stores/mqtt-store'
import FieldSlider from './FieldSlider.vue'
import BaseSegmentedControl from './BaseSegmentedControl.vue'
import BaseButton from './BaseButton.vue'
import WeekdayToggle from './WeekdayToggle.vue'

const props = defineProps<{ chargePointId: number }>()
const mqttStore = useMqttStore()

const plans = computed(() => mqttStore.chargePointChargeTemplate(props.chargePointId)?.time_charging.plans ?? [])

const editing = ref<TimeChargingPlan | null>(null)
const editingIndex = ref<number | null>(null)

const frequencyOptions = [
  { value: 'daily', label: 'Täglich' },
  { value: 'weekly', label: 'Wöchentlich' },
  { value: 'once', label: 'Einmalig' },
] as const

const limitOptions = [
  { value: 'none', label: 'Keine' },
  { value: 'soc', label: 'SoC' },
  { value: 'amount', label: 'Menge' },
] as const

function frequencyLabel(selected: string): string {
  return frequencyOptions.find((o) => o.value === selected)?.label ?? selected
}

function openEdit(plan: TimeChargingPlan, index: number): void {
  // plan is a Vue-reactive Proxy (sourced from the Pinia store) - structuredClone can throw
  // on that in some engines; a JSON round-trip safely unwraps it into plain, editable data
  editing.value = JSON.parse(JSON.stringify(plan)) as TimeChargingPlan
  editingIndex.value = index
}

function openNew(): void {
  const existingIds = plans.value.map((p) => p.id ?? 0)
  editing.value = {
    active: true,
    time: ['06:00', '07:00'],
    frequency: { selected: 'daily', once: [new Date().toISOString().slice(0, 10), new Date().toISOString().slice(0, 10)], weekly: [false, false, false, false, false, false, false] },
    current: 16,
    dc_current: 145,
    id: Math.max(0, ...existingIds) + 1,
    limit: { selected: 'none', soc: 50, amount: 50000 },
    min_bat_soc: null,
    name: 'neuer Zeitladen-Plan',
    phases_to_use: 1,
  }
  editingIndex.value = null
}

function toggleMinBatSoc(enabled: boolean): void {
  if (!editing.value) return
  editing.value.min_bat_soc = enabled ? 50 : null
}

function save(): void {
  if (!editing.value) return
  const next = [...plans.value]
  if (editingIndex.value !== null) next[editingIndex.value] = editing.value
  else next.push(editing.value)
  mqttStore.setChargePointChargeTemplateField(props.chargePointId, 'time_charging.plans', next)
  editing.value = null
}

function remove(): void {
  if (editingIndex.value === null) return
  const next = plans.value.filter((_, i) => i !== editingIndex.value)
  mqttStore.setChargePointChargeTemplateField(props.chargePointId, 'time_charging.plans', next)
  editing.value = null
}
</script>

<style scoped>
.field-label {
  margin-top: 12px;
}
</style>
