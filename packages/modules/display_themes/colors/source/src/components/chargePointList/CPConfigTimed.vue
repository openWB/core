<template>
	<div class="timeplantable p-3 grid12">
		<div class="subtitle grid-col-12">Zeitpläne:</div>
		<div v-if="plans.length == 0" class="warning grid-col-12 p-5">
			Es sind noch keine Pläne definiert. Zeitpläne können in der Web-App
			festgelegt werden.
		</div>

		<div class="subgrid tableheader">
			<span class="grid-col-2"></span>
			<span class="grid-col-3 grid-left">Von</span>
			<span class="grid-col-2">Bis</span>
			<span class="grid-col-2">Ladestrom</span>
			<span class="grid-col-3">Wiederholung</span>
		</div>
		<div
			v-for="(plan, i) in plans"
			:key="i"
			:style="cellStyle(i)"
			class="subgrid tableline"
		>
			<span class="grid-col-2">
				<SwitchInput
					v-model="plan.active"
					@update:model-value="updatePlanState(i)"
				>
				</SwitchInput>
			</span>
			<span class="grid-col-3 grid-left">{{ plan.time[0] }}</span>
			<span class="grid-col-2">{{ plan.time[1] }}</span>
			<span class="grid-col-2">{{ plan.current }}A</span>
			<span class="grid-col-3">{{ freqNames[plan.frequency.selected] }}</span>
		</div>
	</div>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import { timeChargingPlans } from './model'
import { updateServer } from '@/assets/js/sendMessages'
import SwitchInput from '../shared/SwitchInput.vue'

const freqNames: { [key: string]: string } = {
	daily: 'Täglich',
	once: 'Einmal',
	weekly: 'Wöchentlich',
}
const props = defineProps<{
	chargeTemplateId: number
}>()
const plans = computed(() => {
	if (timeChargingPlans[props.chargeTemplateId]) {
		let result = Object.values(timeChargingPlans[props.chargeTemplateId])
		return result ?? []
	} else {
		return []
	}
})
function updatePlanState(i: number) {
	console.log(`update ${i}`)
	updateServer(
		'cpTimedPlanActive',
		plans.value[i].active,
		props.chargeTemplateId,
		i,
	)
}
function cellStyle(key: number) {
	const style = plans.value[key].active ? 'bold' : 'regular'
	return { 'font-weight': style }
}
</script>

<style scoped>
.timeplantable {
	justify-content: center;
	gap: 20px;
}
.subtitle {
	font-size: var(--font-large);
	font-weight: bold;
}
.tableheader {
	color: var(--color-menu);
	background-color: var(--color-bg);
	text-align: center;
	font-style: normal;
	font-size: var(--font-settings);
	font-weight: bold;
}
.tableline {
	color: var(--color-fg);
	background-color: var(--color-bg);
	text-align: center;
	font-size: var(--font-settings);
	margin-top: 0px;
	align-items: center;
}
.warning {
	font-size: var(--font-large);
	font-weight: bold;
	color: var(--color-evu);
}
</style>
