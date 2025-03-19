<template>
	<div class="d-flex flex-column p-3">
		<div class="subtitle mb-4">Pläne für Zielladen:</div>
		<div v-if="plans.length == 0" class="warning p-5">
			Es sind noch keine Pläne definiert. Pläne für das Zielladen können in der
			Web-App festgelegt werden.
		</div>

		<table class="table table-dark">
			<thead>
				<tr>
					<th></th>
					<th>Startzeit</th>
					<th>SoC-Ziel</th>
					<th>SoC-Limit</th>
					<th>Wiederholung</th>
				</tr>
			</thead>
			<tbody>
				<tr v-for="(plan, i) in plans" :key="i" :style="cellStyle(i)">
					<td>
						<SwitchInput
							v-model="plan.active"
							@update:model-value="updatePlanState(i)"
						>
						</SwitchInput>
					</td>
					<td>{{ timeString(i) }}</td>
					<td>{{ plan.limit.soc_scheduled }}%</td>
					<td>{{ plan.limit.soc_limit }}%</td>
					<td>{{ freqNames[plan.frequency.selected] }}</td>
				</tr>
			</tbody>
		</table>
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
.subtitle {
	font-size: var(--font-large);
	font-weight: bold;
}
.warning {
	font-size: var(--font-large);
	font-weight: bold;
	color: var(--color-evu);
}
td {
	background-color: var(--color-bg) !important;
}
th {
	background-color: var(--color-bg) !important;
}
</style>
