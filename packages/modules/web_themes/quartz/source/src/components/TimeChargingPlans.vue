<template>
  <div>
    <template v-if="!editing">
      <span class="field-label mt-3">Zeitfenster</span>
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
        class="field-label mt-3"
        for="tp-name"
      >Name</label>
      <input
        id="tp-name"
        v-model="editing.name"
        type="text"
        class="field-select"
      >

      <div class="toggle-row">
        <label>Aktiv</label>
        <BaseToggle v-model="editing.active" />
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

      <span class="field-label mt-3">Zeitraum</span>
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

      <FieldSlider
        v-if="acChargingEnabled"
        label="Ladestrom"
        unit="A"
        :min="6"
        :max="32"
        :model-value="editing.current"
        @update="(v) => (editing!.current = v)"
      />
      <FieldSlider
        v-if="dcChargingEnabled"
        label="Ladeleistung (DC)"
        unit="kW"
        :min="0"
        :max="dcMaxPower"
        :model-value="convertDcCurrentToPower(editing.dc_current)"
        @update="(v) => (editing!.dc_current = convertPowerToDcCurrent(v))"
      />
      <BaseSegmentedControl
        v-if="acChargingEnabled"
        :model-value="editing.phases_to_use"
        :options="[{ value: 1, label: '1' }, { value: 3, label: 'Maximum' }]"
        @update="(v) => (editing!.phases_to_use = v)"
      />

      <LimitFields
        :limit="editing.limit"
        field-prefix="limit"
        @set="setLimitField"
      />

      <div class="toggle-row">
        <label>Nur wenn Speicher-SoC erreicht</label>
        <BaseToggle
          :model-value="editing.min_bat_soc !== null"
          @update:model-value="toggleMinBatSoc"
        />
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
        class="mt-3.5 w-full"
        @click="save"
      >
        Speichern
      </BaseButton>
    </template>
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import { useMqttStore, type TimeChargingPlan, type Limit } from '@/stores/mqtt-store'
import { convertDcCurrentToPower, convertPowerToDcCurrent } from '@/utils/format'
import { usePlanListEditor, frequencyOptions, frequencyLabel } from '@/composables/usePlanListEditor'
import FieldSlider from './FieldSlider.vue'
import BaseSegmentedControl from './BaseSegmentedControl.vue'
import BaseButton from './BaseButton.vue'
import WeekdayToggle from './WeekdayToggle.vue'
import LimitFields from './LimitFields.vue'
import BaseToggle from './BaseToggle.vue'

const props = defineProps<{ chargePointId: number }>()
const mqttStore = useMqttStore()

const plans = computed(() => mqttStore.chargePointChargeTemplate(props.chargePointId)?.time_charging.plans ?? [])

const acChargingEnabled = computed(() => mqttStore.chargePointChargeType(props.chargePointId) === 'AC')
const dcChargingEnabled = computed(() => mqttStore.chargePointChargeType(props.chargePointId) === 'DC')
const dcMaxPower = computed(() => mqttStore.chargePointDcMaxPower(props.chargePointId) ?? 300)

const { editing, editingIndex, openEdit, openNew, save, remove } = usePlanListEditor<TimeChargingPlan>(
  plans,
  (next) => mqttStore.setChargePointChargeTemplateField(props.chargePointId, 'time_charging.plans', next),
  (existingIds) => ({
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
  }),
)

function toggleMinBatSoc(enabled: boolean): void {
  if (!editing.value) return
  editing.value.min_bat_soc = enabled ? 50 : null
}

function setLimitField(path: string, value: unknown): void {
  if (!editing.value) return
  const field = path.replace('limit.', '') as keyof Limit
  editing.value.limit[field] = value as never
}
</script>
