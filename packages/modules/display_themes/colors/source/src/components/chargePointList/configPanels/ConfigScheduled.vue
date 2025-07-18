<template>
	<div class="d-flex flex-column p-3">
		<div class="subtitle mb-4">Pläne für Zielladen:</div>
		<div v-if="plans.length == 0" class="info p-5">
			Pläne für das Zielladen können in den Einstellungen des Ladeprofils
			angelegt werden.
		</div>
		<table v-else class="table table-dark">
			<thead>
				<tr>
					<th></th>
					<th>Plan</th>
					<th>Zielzeit</th>
					<th>Ladeziel</th>
					<th>Wiederholung</th>
				</tr>
			</thead>
			<tbody>
				<tr v-for="(plan, i) in plans" :key="i" :style="cellStyle(i)">
					<td>
						<SwitchInput
							v-model="plan.active"
							@update:model-value="togglePlanStatus(i)"
						/>
					</td>
					<td>{{ plan.name }}</td>
					<td>{{ timeString(i) }}</td>
					<td>
						{{
							plan.limit.selected == 'soc'
								? plan.limit.soc_scheduled + '%'
								: formatWattH(plan.limit.amount, 0)
						}}
					</td>
					<td>{{ freqNames[plan.frequency.selected] }}</td>
				</tr>
			</tbody>
		</table>
	</div>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import { ChargePoint } from '../model'
import SwitchInput from '@/components/shared/SwitchInput.vue'
import { updateChargeTemplate } from '@/assets/js/sendMessages'
import { formatWattH } from '@/assets/js/helpers'

const freqNames: { [key: string]: string } = {
	daily: 'Täglich',
	once: 'Einmal',
	weekly: 'Wöchentlich',
}
const props = defineProps<{
	chargePoint: ChargePoint
}>()

//computed
const plans = computed(() => {
	return (
		props.chargePoint.chargeTemplate?.chargemode.scheduled_charging.plans ?? []
	)
})

//methods
function timeString(key: number) {
	return plans.value[key].time
}
function cellStyle(key: number) {
	const style = plans.value[key].active ? 'bold' : 'regular'
	return { 'font-weight': style }
}
function togglePlanStatus(i: number) {
	props.chargePoint.chargeTemplate!.chargemode.scheduled_charging.plans[
		i
	]!.active = plans.value[i].active
	updateChargeTemplate(props.chargePoint.id)
}
</script>

<style scoped>
.subtitle {
	font-size: var(--font-large);
	font-weight: bold;
}
.info {
	font-size: var(--font-large);
	font-weight: bold;
	color: var(--color-fg);
}
td {
	background-color: var(--color-bg) !important;
}
th {
	background-color: var(--color-bg) !important;
}
</style>
