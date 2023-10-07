<template>
  <div class="container-fluid p-0 m-0">
    <ConfigItem title="Beginn" :fullwidth="true">
      <TimeInput v-model="plan.time[0]"> </TimeInput>
    </ConfigItem>

    <ConfigItem title="Ende" :fullwidth="true">
      <TimeInput v-model="plan.time[1]"> </TimeInput>
    </ConfigItem>
    <ConfigItem title="Ladestrom" :fullwidth="true">
      <RangeInput
        id="current"
        :min="6"
        :max="32"
        :step="1"
        unit="A"
        v-model="plan.current"
      ></RangeInput>
    </ConfigItem>
    <ConfigItem title="Wiederholungen" :fullwidth="true">
      <SelectInput
        :options="frequencies"
        v-model="plan.frequency.selected"
      ></SelectInput>
    </ConfigItem>
    <ConfigItem
      v-if="plan.frequency.selected == 'once'"
      title="Gültig ab" :fullwidth="true"
    >
      <DateInput v-model="plan.frequency.once[0]"> </DateInput>
    </ConfigItem>
    <ConfigItem
      v-if="plan.frequency.selected == 'once'"
      title="Gültig bis" :fullwidth="true"
    >
      <DateInput v-model="plan.frequency.once[1]"> </DateInput>
    </ConfigItem>
    <ConfigItem
      v-if="plan.frequency.selected == 'weekly'"
      title="Wochentage" :fullwidth="true"
    >
      <CheckBoxInput
        :options="days"
        v-model="plan.frequency.weekly"
      ></CheckBoxInput>
    </ConfigItem>
    <div class="row">
      <div class="col d-flex justify-content-end">
        <button
          class="btn btn-danger"
          @click="$emit('deletePlan', planId)"
          
        >
          Löschen
        </button>
        <button
          class="btn btn-warning ms-1"
          @click="$emit('abort')"
        
        >
          Abbrechen
        </button>
        <button
          class="btn btn-success float-end ms-1"
          @click="$emit('savePlan', planId)"
          
        >
          Speichern
        </button>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import { chargeTemplates, createChargeTimePlan } from '../model'
import ConfigItem from '../../shared/ConfigItem.vue'
import RangeInput from '@/components/shared/RangeInput.vue'
import SelectInput from '@/components/shared/SelectInput.vue'
import CheckBoxInput from '@/components/shared/CheckBoxInput.vue'
import TimeInput from '@/components/shared/TimeInput.vue'
import DateInput from '@/components/shared/DateInput.vue'
const props = defineProps<{
  chargeTemplateId: number
  planId: string
}>()
const emit = defineEmits(['deletePlan', 'abort', 'savePlan'])

const frequencies: [string | number, string | number][] = [
  ['Einmalig', 'once'],
  ['Täglich', 'daily'],
  ['Wöchentlich', 'weekly'],
]
const days = [
  'Montag',
  'Dienstag',
  'Mittwoch',
  'Donnerstag',
  'Freitag',
  'Samstag',
  'Sonntag',
]
const template = computed(() => {
  return chargeTemplates[props.chargeTemplateId]
})
const plan = computed(() => {
  let p = template.value.time_charging.plans[props.planId]
  if (p) {
    return p
  } else {
    return createChargeTimePlan() // create a dummy time plan in case the list of plans in the template is empty
  }
})
</script>

<style scoped>
.time-input {
  background-color: var(--color-bg);
  color: var(--color-fg);
  border: 1px solid var(--color-menu);
}
</style>
