<template>
  <div class="container-fluid p-0 m-0">
    <ConfigItem title="Ladestand" :fullwidth="true">
       <RangeInput
        id="soc"
        :min="0"
        :max="100"
        :step="1"
        unit="%"
        v-model="plan.soc"
      ></RangeInput>
      
    </ConfigItem>
    <ConfigItem title="Zielzeit beachten" :fullwidth="true">
      <SwitchInput v-model="plan.timed"></SwitchInput>
    </ConfigItem>
    <ConfigItem title="Uhrzeit" :fullwidth="true">
      <TimeInput v-model="plan.time"> </TimeInput>
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
    <div class="row mt-2">
      <div class="col d-flex justify-content-end">
        <button
          class="btn btn-danger"
          @click="$emit('deletePlan', planId)"
          data-bs-dismiss="modal"
        >
          Löschen
        </button>
        <button
          class="btn btn-warning ms-1"
          @click="$emit('abort')"
          data-bs-dismiss="modal"
        >
          Abbrechen
        </button>
        <button
          class="btn btn-success float-end ms-1"
          @click="$emit('savePlan', planId)"
          data-bs-dismiss="modal"
        >
          Speichern
        </button>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import { chargeTemplates, createChargeSchedule } from '../model'
import ConfigItem from '../../shared/ConfigItem.vue'
import RangeInput from '@/components/shared/RangeInput.vue'
import SelectInput from '@/components/shared/SelectInput.vue'
import CheckBoxInput from '@/components/shared/CheckBoxInput.vue'
import TimeInput from '@/components/shared/TimeInput.vue'
import DateInput from '@/components/shared/DateInput.vue'
import SwitchInput from '../../shared/SwitchInput.vue'
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
  let p = template.value.chargemode.scheduled_charging.plans[props.planId]
  if (p) { 
  return p
  } else {
    return createChargeSchedule() // create a dummy time plan in case the list of plans in the template is empty
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
