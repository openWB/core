<template>
	<div class="schedulestable p-3 grid12">
		<div class="subtitle grid-col-12">Pläne für Zielladen:</div>
		<div v-if="plans.length == 0" class="warning grid-col-12 p-5">
			Es sind noch keine Pläne definiert. Pläne für das Zielladen können in der
			Web-App festgelegt werden.
		</div>
		<div class="subgrid tableheader">
			<span class="grid-col-2 grid-left"></span>
			<span class="grid-col-3 grid-left">Startzeit</span>
			<span class="grid-col-2">SoC-Ziel</span>
			<span class="grid-col-2">SoC-Limit</span>
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
			<span class="grid-col-3 grid-left">{{ timeString(i) }}</span>
			<span class="grid-col-2">{{ plan.limit.soc_scheduled }}%</span>
			<span class="grid-col-2">{{ plan.limit.soc_limit }}%</span>
			<span class="grid-col-3">{{ freqNames[plan.frequency.selected] }}</span>
		</div>
	</div>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import { scheduledChargingPlans } from './model'
import SwitchInput from '../shared/SwitchInput.vue'
import { updateServer } from '@/assets/js/sendMessages'

const freqNames: { [key: string]: string } = {
	daily: 'Täglich',
	once: 'Einmal',
	weekly: 'Wöchentlich',
}
const props = defineProps<{
	chargeTemplateId: number
}>()
//computed
const plans = computed(() =>
	scheduledChargingPlans[props.chargeTemplateId]
		? Object.values(scheduledChargingPlans[props.chargeTemplateId])
		: [],
)

function updatePlanState(i: number) {
	console.log(`update ${i}`)
	updateServer(
		'cpScheduledPlanActive',
		plans.value[i].active,
		props.chargeTemplateId,
		i,
	)
}

//methods
function timeString(key: number) {
	return plans.value[key].time
}
function cellStyle(key: number) {
	const style = plans.value[key].active ? 'bold' : 'regular'
	return { 'font-weight': style }
}
</script>

<style scoped>
.schedulestable {
	justify-content: center;
	gap: 20px;
}
.tableline {
	color: var(--color-fg);
	background-color: var(--color-bg);
	text-align: center;
	font-size: var(--font-settings);
	margin-top: 0px;
	align-items: center;
}
.tableheader {
	color: var(--color-menu);
	background-color: var(--color-bg);
	text-align: center;
	font-style: normal;
	font-size: var(--font-settings);
	font-weight: bold;
}
.subtitle {
	font-size: var(--font-large);
	font-weight: bold;
}
.warning {
	font-size: var(--font-large);
	font-weight: bold;
	color: var(--color-evu);
}
</style>
