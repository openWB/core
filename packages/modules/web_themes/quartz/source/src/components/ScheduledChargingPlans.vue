<template>
  <div>
    <template v-if="!editing">
      <span class="field-label mt-3">Termine Zielladen</span>
      <p
        v-if="plans.length === 0"
        class="mode-note"
      >
        Keine Termine konfiguriert.
      </p>
      <div
        v-for="(plan, index) in plans"
        :key="plan.id ?? index"
        class="plan-row"
        @click="openEdit(plan, index)"
      >
        <span>
          {{ plan.name }} &middot; {{ plan.time }} Uhr
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
        + Neuer Termin
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
        class="field-label mt-3"
        for="sp-name"
      >Name</label>
      <input
        id="sp-name"
        v-model="editing.name"
        type="text"
        class="field-select"
      >

      <div class="toggle-row">
        <label for="sp-active">Aktiv</label>
        <input
          id="sp-active"
          v-model="editing.active"
          type="checkbox"
        >
      </div>

      <label
        class="field-label mt-3"
        for="sp-time"
      >Zielzeit</label>
      <input
        id="sp-time"
        v-model="editing.time"
        type="time"
        class="field-select"
      >

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
      <input
        v-if="editing.frequency.selected === 'once'"
        v-model="editing.frequency.once"
        type="date"
        class="field-select"
      >

      <BaseSegmentedControl
        label="Begrenzung"
        :model-value="editing.limit.selected"
        :options="scheduledLimitOptions"
        @update="editing.limit.selected = $event"
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
      <template v-else>
        <FieldSlider
          label="Ziel-SoC"
          unit="%"
          :min="0"
          :max="100"
          :model-value="editing.limit.soc_scheduled"
          @update="(v) => (editing!.limit.soc_scheduled = v)"
        />
        <FieldSlider
          label="Maximal-SoC für Überschussladen danach"
          unit="%"
          :min="0"
          :max="100"
          :model-value="editing.limit.soc_limit"
          @update="(v) => (editing!.limit.soc_limit = v)"
        />
      </template>

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
        :options="[{ value: 1, label: '1' }, { value: 3, label: 'Maximum' }, { value: 0, label: 'Automatik' }]"
        @update="(v) => (editing!.phases_to_use = v)"
      />

      <BaseButton
        variant="primary"
        class="mt-3.5 w-full"
        @click="save"
      >
        Speichern
      </BaseButton>
    </template>
  </div>
</template>

<script setup lang="ts">
import { computed, ref } from 'vue'
import { useMqttStore, type ScheduledChargingPlan } from '@/stores/mqtt-store'
import FieldSlider from './FieldSlider.vue'
import BaseSegmentedControl from './BaseSegmentedControl.vue'
import BaseButton from './BaseButton.vue'
import WeekdayToggle from './WeekdayToggle.vue'

const props = defineProps<{ chargePointId: number }>()
const mqttStore = useMqttStore()

const plans = computed(() => mqttStore.chargePointChargeTemplate(props.chargePointId)?.chargemode.scheduled_charging.plans ?? [])

const editing = ref<ScheduledChargingPlan | null>(null)
const editingIndex = ref<number | null>(null)

const frequencyOptions = [
  { value: 'daily', label: 'Täglich' },
  { value: 'weekly', label: 'Wöchentlich' },
  { value: 'once', label: 'Einmalig' },
] as const

const scheduledLimitOptions = [
  { value: 'amount', label: 'Menge' },
  { value: 'soc', label: 'SoC' },
] as const

function frequencyLabel(selected: string): string {
  return frequencyOptions.find((o) => o.value === selected)?.label ?? selected
}

function openEdit(plan: ScheduledChargingPlan, index: number): void {
  // plan is a Vue-reactive Proxy (sourced from the Pinia store) - structuredClone can throw
  // on that in some engines; a JSON round-trip safely unwraps it into plain, editable data
  editing.value = JSON.parse(JSON.stringify(plan)) as ScheduledChargingPlan
  editingIndex.value = index
}

function openNew(): void {
  const existingIds = plans.value.map((p) => p.id ?? 0)
  editing.value = {
    active: true,
    time: '07:00',
    frequency: { selected: 'daily', once: new Date().toISOString().slice(0, 10), weekly: [false, false, false, false, false, false, false] },
    current: 14,
    dc_current: 145,
    id: Math.max(0, ...existingIds) + 1,
    name: 'neuer Zielladen-Plan',
    limit: { selected: 'amount', amount: 1000, soc_limit: 90, soc_scheduled: 80 },
    phases_to_use: 0,
    phases_to_use_pv: 0,
    bidi_charging_enabled: false,
    bidi_power: 10000,
    et_active: false,
  }
  editingIndex.value = null
}

function save(): void {
  if (!editing.value) return
  const next = [...plans.value]
  if (editingIndex.value !== null) next[editingIndex.value] = editing.value
  else next.push(editing.value)
  mqttStore.setChargePointChargeTemplateField(props.chargePointId, 'chargemode.scheduled_charging.plans', next)
  editing.value = null
}

function remove(): void {
  if (editingIndex.value === null) return
  const next = plans.value.filter((_, i) => i !== editingIndex.value)
  mqttStore.setChargePointChargeTemplateField(props.chargePointId, 'chargemode.scheduled_charging.plans', next)
  editing.value = null
}
</script>
