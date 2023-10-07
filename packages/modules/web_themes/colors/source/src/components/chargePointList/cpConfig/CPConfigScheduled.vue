<template>
    <p class="heading ms-1 pt-2">Zielladen:</p>
    <table class="table table-borderless">
      <thead>
        <tr>
          <th class="tableheader">Ziel-SoC</th>
          <th class="tableheader">Zeit</th>
          <th class="tableheader">Wiederholung</th>
          <th class="tableheader"></th>
        </tr>
      </thead>
      <tbody>
        <tr v-for="key in Object.keys(plans)">
          <td class="tablecell">{{ plans[key].soc }} %</td>
          <td class="tablecell">{{ timeString(key) }}</td>
          <td class="tablecell">
            {{ freqNames[plans[key].frequency.selected] }}
          </td>
          <td class="tablecell left">
            <span
              class="editButton"
              data-bs-toggle="modal"
              :data-bs-target="'#' + modalId"
              @click="setPlanToEdit(key)"
            >
              <i class="fas fa-lg fa-pen ms-2"></i>
            </span>
          </td>
        </tr>
        <tr>
          <td class="emptycell"></td>
          <td class="emptycell"></td>
          <td class="emptycell"></td>
          <td class="right">
            <span
              class="addButton"
              @click="addPlan"
              :data-bs-target="'#' + modalId"
            >
              <i class="fa-solid fa-xl fa-square-plus ms-2"></i>
            </span>
          </td>
        </tr>
      </tbody>
    </table>

    <ModalComponent v-for="planId in plansToEdit" :modalId="modalId">
      <template v-slot:title> Zielladen - Parameter </template>
      <CPEditSchedule
        :chargeTemplateId="chargeTemplateId"
        :planId="planId"
        @savePlan="savePlan"
        @deletePlan="deletePlan"
        @abort="abortEdit"
      ></CPEditSchedule>
    </ModalComponent>

</template>

<script setup lang="ts">
import { reactive, computed } from 'vue'
import { Modal } from 'bootstrap'
import type { ChargeTemplate, ChargeSchedule } from '../model'
import { createChargeSchedule } from '../model'
import ModalComponent from '@/components/shared/ModalComponent.vue'
import CPEditSchedule from './CPEditSchedule.vue'
import { updateChargeTemplate } from '@/assets/js/sendMessages'

const freqNames: { [key: string]: string } = {
  daily: 'Täglich',
  once: 'Einmal',
  weekly: 'Wöchentlich',
}
const props = defineProps<{
  chargeTemplate: ChargeTemplate
  chargeTemplateId: number
}>()

const modalId = 'schedulesettingmodal' + props.chargeTemplateId
// const planIdToEdit = (Object.keys(props.chargeTemplate.time_charging.plans).length >0) ? ref(Object.keys(props.chargeTemplate.time_charging.plans)[0]) : ref('0')
const plansToEdit: string[] = reactive(['0'])
//computed
const plans = computed(() => {
  let result = props.chargeTemplate.chargemode.scheduled_charging.plans
  return result ? result : {}
})
//methods
function timeString(key: string) {
  return plans.value[key].timed ? plans.value[key].time : '-'
}
function setPlanToEdit(key: string) {
  plansToEdit[0] = key
}
function savePlansToServer(id: string) {
  updateChargeTemplate(props.chargeTemplateId)
}
function savePlan(id: string) {
  savePlansToServer(id)
}
function abortEdit() {
  console.log('abort edit')
}
function deletePlan(id: string) {
  delete props.chargeTemplate.chargemode.scheduled_charging.plans[id]
  savePlansToServer(id)
}
function addPlan() {
  let p: ChargeSchedule = createChargeSchedule()
  if (!props.chargeTemplate.chargemode.scheduled_charging.plans) {
    props.chargeTemplate.chargemode.scheduled_charging.plans = {}
  }
  let max = 0
  Object.keys(plans.value).forEach((k) => {
    if (+k > max) {
      max = +k
    }
  })
  max = max + 1
  props.chargeTemplate.chargemode.scheduled_charging.plans[max.toString()] = p
  setPlanToEdit(max.toString())
  console.log(plans.value)
  showModal()
}
function showModal() {
  let element = document.getElementById(modalId)
  if (element) {
    let modal = new Modal(element)
    modal.show()
  } else {
    console.log('NO MODAL ELEMENT')
  }
}
</script>

<style scoped>
.tablecell {
  color: var(--color-fg);
  text-align: center;
}
.emptycell {
  border-left: 0;
  border-right: 0;
  border-bottom: 0;
}
.tableheader {
  color: var(--color-menu);
  text-align: center;
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
