<template>
    <p class="heading ms-1 pt-2">Zeitpläne:</p>
    <table class="table table-borderless">
      <thead>
        <tr>
          <th class="tableheader ">Von</th>
          <th class="tableheader">Bis</th>
          <th class="tableheader">Ladestrom</th>
          <th class="tableheader ">Wiederholung</th>
          <th class="tableheader right"></th>
        </tr>
      </thead>
      <tbody>
        <tr v-for="key in Object.keys(plans)">
          <td class="tablecell">{{ plans[key].time[0] }}</td>
          <td class="tablecell">{{ plans[key].time[1] }}</td>
          <td class="tablecell">{{ plans[key].current }} A</td>
          <td class="tablecell">
            {{ freqNames[plans[key].frequency.selected] }}
          </td>
          <td class="tablecell left">
            <span
              class="editButton"
             @click="setPlanToEdit(key);editPlan=true"
            >
              <i class="fas fa-lg fa-pen ms-2"></i>
            </span>
          </td>
        </tr>
        <tr>
          <td class="emptycell"></td>
          <td class="emptycell"></td>
          <td class="emptycell"></td>
          <td class="emptycell"></td>
          <td class="tablecell right">
            <span
              class="addButton"
              @click="addPlan"
            >
              <i class="fa-solid fa-xl fa-square-plus ms-2"></i>
            </span>
          </td>
        </tr>
      </tbody>
    </table>
  
    <WBWidget :full-width="true" v-if="editPlan" >
      <template v-slot:title> Zeitplan bearbeiten </template>
      <CPEditTimeplan
        :chargeTemplateId ="chargeTemplateId"
        :planId="plansToEdit[0]"
        @savePlan="savePlan"
        @deletePlan="deletePlan"
        @abort="abortEdit"
      ></CPEditTimeplan>
    </WBWidget>
</template>

<script setup lang="ts">
import { ref, reactive, computed } from 'vue'
import type { ChargeTemplate, ChargeTimePlan } from '../model'
import { createChargeTimePlan } from '../model'
import CPEditTimeplan from './CPEditTimeplan.vue'
import WBWidget from '@/components/shared/WBWidget.vue'
import { updateChargeTemplate } from '@/assets/js/sendMessages'

const freqNames : {[key:string]:string} = {
  'daily': 'Täglich',
  'once': 'Einmal',
  'weekly': 'Wöchentlich'
}
const props = defineProps<{
  chargeTemplate: ChargeTemplate
  chargeTemplateId: number
}>()

// const planIdToEdit = (Object.keys(props.chargeTemplate.time_charging.plans).length >0) ? ref(Object.keys(props.chargeTemplate.time_charging.plans)[0]) : ref('0')
const plansToEdit : string[] = reactive(["0"])
function setPlanToEdit(key: string) {
  plansToEdit[0] = key
}
const editPlan = ref(false)
function savePlansToServer(id: string) {
  updateChargeTemplate(props.chargeTemplateId)
}
function savePlan(id: string) {
  savePlansToServer(id)
  editPlan.value=false
}
function abortEdit() {
  console.log('abort edit')
  editPlan.value=false
 }
function deletePlan(id: string) {
  delete props.chargeTemplate.time_charging.plans[id]
  savePlansToServer(id)
  editPlan.value=false
}
function addPlan() {
  let p: ChargeTimePlan = createChargeTimePlan()
  if (!(props.chargeTemplate.time_charging.plans)) {
    props.chargeTemplate.time_charging.plans={}
  }
  let max = 0
  Object.keys(plans.value).forEach((k) => {
    if (+k > max) {
      max = +k
    }
  })
  max = max + 1
  props.chargeTemplate.time_charging.plans[max.toString()] = p
  setPlanToEdit (max.toString())
  // showModal()
  editPlan.value=true
}

const plans = computed(() => {
  let result = props.chargeTemplate.time_charging.plans
  return (result)? result : {}
  })
</script>

<style scoped>
.tablecell {
  color: var(--color-fg);
  background-color: var(--color-bg);
  text-align: center;
 }
.tableheader {
  color: var(--color-menu);
  background-color: var(--color-bg);
  text-align: center;
 }
 .emptycell {
  border-left: 0;
  border-right: 0;
  border-bottom: 0;
  border-top: 0;
  background-color: var(--color-bg);
  color: var(--color-fg);
}
.heading {
  color: var(--color-battery);
}
.editButton {
  color: var(--color-menu);
}
.addButton {
  color: var(--color-menu);
}
.left {
  text-align: left;
}
.right {
  text-align: right;
}
</style>
