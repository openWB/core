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
        :disabled="addPending"
        @click="openNew"
      >
        + Neuer Termin
      </button>
    </template>

    <template v-else>
      <div class="plan-edit-head">
        <BaseButton @click="cancel">
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
        <label>Aktiv</label>
        <BaseToggle
          v-model="editing.active"
          label="Aktiv"
        />
      </div>

      <BaseSegmentedControl
        label="Häufigkeit"
        :model-value="editing.frequency.selected"
        :options="frequencyOptions"
        @update="(v) => setFrequency(editing!.frequency, v)"
      />
      <WeekdayToggle
        v-if="editing.frequency.selected === 'weekly'"
        :model-value="editing.frequency.weekly"
        @update="(v) => (editing!.frequency.weekly = v)"
      />

      <span class="field-label mt-3">Ziel-Termin</span>
      <div class="flex gap-3">
        <div class="flex-1">
          <label class="field-label">Ziel-Datum</label>
          <input
            v-if="editing.frequency.selected === 'once'"
            v-model="editing.frequency.once"
            type="date"
            class="field-select"
          >
          <input
            v-else
            type="date"
            class="field-select"
            disabled
          >
        </div>
        <div class="flex-1">
          <label
            class="field-label"
            for="sp-time"
          >Ziel-Uhrzeit</label>
          <input
            id="sp-time"
            v-model="editing.time"
            type="time"
            class="field-select"
          >
        </div>
      </div>
      <div class="info-box mt-2">
        <strong>Nächster geplanter Termin:</strong>
        {{ nextOccurrenceLabel }} &middot; {{ editing.time }} Uhr &middot;
        <template v-if="editing.limit.selected === 'soc'">
          {{ editing.limit.soc_scheduled }}%
          <component
            :is="editing.bidi_charging_enabled ? IconSyncAlt : IconArrowRight"
            class="inline-block align-text-bottom"
          />
          {{ editing.limit.soc_limit }}%
        </template>
        <template v-else>
          {{ targetLabel }}
        </template>
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
        label="Anzahl Phasen Zielladen"
        :model-value="editing.phases_to_use"
        :options="[{ value: 1, label: '1' }, { value: 3, label: 'Maximum' }, { value: 0, label: 'Automatik' }]"
        @update="(v) => (editing!.phases_to_use = v)"
      />
      <BaseSegmentedControl
        v-if="acChargingEnabled"
        label="Anzahl Phasen bei PV-Überschuss"
        :model-value="editing.phases_to_use_pv"
        :options="[{ value: 1, label: '1' }, { value: 3, label: 'Maximum' }, { value: 0, label: 'Automatik' }]"
        @update="(v) => (editing!.phases_to_use_pv = v)"
      />

      <BaseSegmentedControl
        label="Ziel"
        :model-value="editing.limit.selected"
        :options="scheduledLimitOptions.map((o) => ({ ...o, disabled: o.value === 'soc' && !socAvailable }))"
        @update="editing.limit.selected = $event"
      />
      <template v-if="editing.limit.selected === 'soc'">
        <FieldSlider
          label="EV-SoC"
          unit="%"
          :min="0"
          :max="100"
          :model-value="editing.limit.soc_scheduled"
          @update="(v) => (editing!.limit.soc_scheduled = v)"
        />
        <FieldSlider
          label="Fahrzeug-SoC mit Überschuss"
          unit="%"
          :min="0"
          :max="100"
          :model-value="editing.limit.soc_limit"
          @update="(v) => (editing!.limit.soc_limit = v)"
        />
      </template>
      <FieldSlider
        v-else
        label="Ziel-Energie"
        unit="kWh"
        :min="0"
        :max="100"
        :decimals="1"
        :model-value="editing.limit.amount / 1000"
        @update="(v) => (editing!.limit.amount = Math.round(v * 1000))"
      />

      <template v-if="editing.limit.selected === 'soc' && bidiCapable">
        <div class="toggle-row">
          <label>Bidirektionales Überschussladen</label>
          <BaseToggle
            v-model="editing.bidi_charging_enabled"
            label="Bidirektionales Überschussladen"
          />
        </div>
        <FieldSlider
          v-if="editing.bidi_charging_enabled"
          label="Bidirektionale Ladeleistung"
          unit="kW"
          :min="0"
          :max="22"
          :step="0.5"
          :decimals="1"
          :model-value="editing.bidi_power / 1000"
          @update="(v) => (editing!.bidi_power = Math.round(v * 1000))"
        />
      </template>

      <div class="toggle-row">
        <label>Strompreisbasiert laden</label>
        <BaseToggle
          v-model="editing.et_active"
          label="Strompreisbasiert laden"
        />
      </div>

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
import { useMqttStore, type ScheduledChargingPlan } from '@/stores/mqtt-store'
import { convertDcCurrentToPower, convertPowerToDcCurrent } from '@/utils/format'
import { formatDateDDMMYYYY, nextRunDate, setFrequency } from '@/utils/planSchedule'
import { usePlanListEditor, frequencyOptions, frequencyLabel } from '@/composables/usePlanListEditor'
import FieldSlider from './FieldSlider.vue'
import BaseSegmentedControl from './BaseSegmentedControl.vue'
import BaseButton from './BaseButton.vue'
import WeekdayToggle from './WeekdayToggle.vue'
import IconSyncAlt from './icons/IconSyncAlt.vue'
import IconArrowRight from './icons/IconArrowRight.vue'
import BaseToggle from './BaseToggle.vue'

const props = defineProps<{ chargePointId: number }>()
const mqttStore = useMqttStore()

const plans = computed(() => mqttStore.chargePointChargeTemplate(props.chargePointId)?.chargemode.scheduled_charging.plans ?? [])
// the vehicle's EV template must support bidi, independent of the hardware
const bidiCapable = computed(() => mqttStore.chargePointConnectedVehicleBidiCapable(props.chargePointId))

const socAvailable = computed(() => mqttStore.chargePointConnectedVehicleSocType(props.chargePointId) !== undefined)

const acChargingEnabled = computed(() => mqttStore.chargePointChargeType(props.chargePointId) === 'AC')
const dcChargingEnabled = computed(() => mqttStore.chargePointChargeType(props.chargePointId) === 'DC')
const dcMaxPower = computed(() => mqttStore.chargePointDcMaxPower(props.chargePointId) ?? 300)

const { editing, editingIndex, addPending, openEdit, openNew, save, cancel, remove } = usePlanListEditor<ScheduledChargingPlan>(
  plans,
  (next) => mqttStore.setChargePointChargeTemplateField(props.chargePointId, 'chargemode.scheduled_charging.plans', next),
  () => mqttStore.addChargePlan(props.chargePointId, 'scheduled'),
)

const nextOccurrenceLabel = computed(() => {
  if (!editing.value) return ''
  const next = nextRunDate(editing.value.frequency, editing.value.time, new Date())
  return next ? formatDateDDMMYYYY(next) : '-'
})

const targetLabel = computed(() => {
  if (!editing.value) return ''
  const limit = editing.value.limit
  return limit.selected === 'soc'
    ? `${limit.soc_scheduled}%`
    : `${(limit.amount / 1000).toLocaleString(undefined, { maximumFractionDigits: 1 })} kWh`
})

const scheduledLimitOptions = [
  { value: 'soc', label: 'EV-SoC' },
  { value: 'amount', label: 'Energie' },
] as const
</script>
