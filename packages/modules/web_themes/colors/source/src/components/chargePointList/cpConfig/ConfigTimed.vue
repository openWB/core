<template>
	<ConfigItem title="Zeitladen aktiv" icon="fa-clock" :fullwidth="true">
		<template #inline-item>
			<SwitchInput v-model="cp.timedCharging" />
		</template>
	</ConfigItem>
	<p class="heading pt-2">Zeitpläne:</p>
	<div class="plantable">
		<div
			v-for="(plan, i) in plans"
			:key="i"
			class="plandisplay"
			:style="fontcolor(i)"
		>
			<span class="planbuttons-left">
				<i
					class="planswitch fa fa-xl"
					:class="plan.active ? 'fa-toggle-on' : 'fa-toggle-off'"
					:style="switchStyle(i)"
					type="button"
					@click="toggleSwitch(i)"
				/>
			</span>
			<span class="targettime"> {{ timeString(i) }} </span>
			<span class="planbuttons-right">
				<i class="fa-solid fa-xl fa-gear" @click="openEditor(i)" />
			</span>
			<span v-if="plan.frequency.selected != 'weekly'" class="frequency mt-2">
				{{ frequencyString(i) }}
			</span>
			<div v-else class="frequency mt-2">
				<i
					v-for="(b, d) in plan.frequency.weekly"
					:key="d"
					:class="
						'fa-solid fa-xs ' + (b ? 'fa-charging-station' : 'fa-circle-xmark')
					"
				>
				</i>
			</div>
			<span class="planname mt-2">{{ plan.name }}</span>
			<hr class="dividerline" />
		</div>
	</div>
	<button class="createButton btn btn-sm" @click="addPlan">Neuer Plan</button>

	<EditTimeplan
		v-for="plan in plans"
		:key="plan.id"
		:model-value="plan"
		:cp-id="chargePoint.id"
		@update:model-value="savePlan"
		@delete-plan="deletePlan"
	/>
</template>

<script setup lang="ts">
import { computed, ref } from 'vue'
import { ChargePoint, type ChargeTimePlan } from '../model'
import { sendCommand, updateChargeTemplate } from '@/assets/js/sendMessages'
import { Modal } from 'bootstrap'
import SwitchInput from '@/components/shared/SwitchInput.vue'
import ConfigItem from '../../shared/ConfigItem.vue'
import EditTimeplan from './EditTimeplan.vue'

const props = defineProps<{
	chargePoint: ChargePoint
}>()

var editorModal = ref<Modal | null>(null)
const planToEdit = ref<number>(0)
const cp = props.chargePoint
const plans = computed(
	() =>
		props.chargePoint?.chargeTemplate?.time_charging.plans ??
		([] as ChargeTimePlan[]),
)
function frequencyString(i: number): string {
	switch (plans.value[i].frequency.selected) {
		case 'once':
			return dateString(plans.value[i].frequency.once!)
		case 'daily':
			return 'täglich'
		case 'weekly':
			return ''
		default:
			return ''
	}
}
function timeString(key: number) {
	return `${plans.value[key].time[0]} -> ${plans.value[key].time[1]}`
}
function dateString(s: [string, string]) {
	const elts0 = s[0].split('-')
	const elts1 = s[1].split('-')

	return `${Number(elts0[2])}.${Number(elts0[1])}.-${Number(elts1[2])}.${Number(elts1[1])}`
}

function switchStyle(key: number) {
	const style = plans.value[key].active
		? 'var(--color-switchGreen)'
		: 'var(--color-switchRed)'
	return { color: style }
}

function fontcolor(i: number) {
	return {
		color: plans.value[i].active ? 'var(--color-fg)' : 'var(--color-menu)',
	}
}
function toggleSwitch(i: number) {
	props.chargePoint.chargeTemplate!.time_charging.plans[i]!.active =
		!plans.value[i].active
	updateChargeTemplate(props.chargePoint.id)
}
function openEditor(plan: number) {
	const modalId = `timePlanSettings-${props.chargePoint.id}-${plans.value[plan]!.id}`
	planToEdit.value = plan
	editorModal.value = new Modal(document.getElementById(modalId)!)
	editorModal.value.toggle()
}
function savePlan() {
	editorModal.value!.hide()
	updateChargeTemplate(props.chargePoint.id)
}
function addPlan() {
	sendCommand({
		command: 'addChargeTemplateTimeChargingPlan',
		data: {
			template: props.chargePoint.chargeTemplate!.id,
			chargepoint: props.chargePoint.id,
			changed_in_theme: true,
		},
	})
}
function deletePlan() {
	editorModal.value!.hide()
	sendCommand({
		command: 'removeChargeTemplateTimeChargingPlan',
		data: {
			template: props.chargePoint.chargeTemplate!.id,
			plan: plans.value[planToEdit.value]!.id,
			chargepoint: props.chargePoint.id,
			changed_in_theme: true,
		},
	})
}
</script>

<style scoped>
.plantable {
	display: grid;
	grid-template-columns: repeat (2, 1fr) repeat (8, auto) repeat(2, 1fr);
	font-size: var(--font-settings);
}
.plandisplay {
	display: grid;
	grid-column: 1 / 13;
	grid-template-columns: subgrid;
}
.planbuttons-right {
	grid-column: span 2;
	text-align: right;
}
.planbuttons-left {
	grid-column: span 2;
	text-align: left;
}
.planname {
	grid-column: span 8;
	text-align: right;
}
.frequency {
	grid-column: span 4;
	text-align: left;
}
.targettime {
	grid-column: span 8;
	text-align: center;
	font-weight: bold;
}
.limit {
	grid-column: span 4;
	text-align: right;
}
.heading {
	color: var(--color-battery);
	font-size: var(--font-settings);
	font-weight: bold;
}
.fa-gear {
	color: var(--color-charging);
	cursor: pointer;
}
.fa-trash {
	color: var(--color-evu);
	cursor: pointer;
}
.fa-charging-station {
	color: var(--color-charging);
}
.fa-circle-xmark {
	color: var(--color-evu);
}
.createButton {
	background-color: var(--color-bg);
	color: var(--color-charging);
	font-size: var(--font-settings-button);
	width: 100%;
}
.dividerline {
	grid-column: span 12;
}
.tablecell {
	color: var(--color-fg);
	background-color: var(--color-bg);
	text-align: center;
	font-size: var(--font-settings);
}
.tableheader {
	color: var(--color-menu);
	background-color: var(--color-bg);
	text-align: center;
	font-style: normal;
}

.heading {
	color: var(--color-battery);
	font-size: var(--font-settings);
	font-weight: bold;
}

.left {
	text-align: left;
}
.right {
	text-align: right;
}
.text-bold {
	font-weight: bold;
}
.text-normal {
	font-weight: normal;
}
.fa-circle-info {
	color: var(--color-charging);
	cursor: pointer;
}
.fa-gear {
	color: var(--color-charging);
	cursor: pointer;
}
</style>
