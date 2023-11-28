<template>
	<p class="heading ms-1 pt-2">Zielladen:</p>
	<table class="table table-borderless">
		<thead>
			<tr>
				<th class="tableheader">Ziel</th>
				<th class="tableheader">Limit</th>
				<th class="tableheader">Zeit</th>
				<th class="tableheader">Wiederholung</th>
				<th class="tableheader" />
			</tr>
		</thead>
		<tbody>
			<tr v-for="(plan, i) in plans" :key="i" :style="cellStyle(i)">
				<td class="tablecell">{{ plan.limit.soc_scheduled }}%</td>
				<td class="tablecell">{{ plan.limit.soc_limit }}%</td>
				<td class="tablecell">
					{{ timeString(i) }}
				</td>
				<td class="tablecell">
					{{ freqNames[plan.frequency.selected] }}
				</td>
				<td class="tablecell left">
					<a
						:href="
							'../../settings/#/VehicleConfiguration/charge_template/' +
							props.chargeTemplateId
						"
					>
						<span
							:class="plan.active ? 'fa-toggle-on' : 'fa-toggle-off'"
							:style="switchStyle(i)"
							class="fa"
							type="button"
						>
						</span
					></a>
				</td>
			</tr>
		</tbody>
	</table>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import { scheduledChargingPlans, type ChargeSchedule } from '../model'

const freqNames: { [key: string]: string } = {
	daily: 'Täglich',
	once: 'Einmal',
	weekly: 'Wöchentlich',
}
const props = defineProps<{
	chargeTemplateId: number
}>()

//computed
const plans = computed(() => {
	let result: ChargeSchedule[] = []
	if (scheduledChargingPlans[props.chargeTemplateId]) {
		result = Object.values(scheduledChargingPlans[props.chargeTemplateId])
	}
	return result
})
//methods
function timeString(key: number) {
	return plans.value[key].time
}
function switchStyle(key: number) {
	const style = plans.value[key].active
		? 'var(--color-switchGreen)'
		: 'var(--color-switchRed)'
	return { color: style }
}
function cellStyle(key: number) {
	const style = plans.value[key].active ? 'bold' : 'regular'
	return { 'font-weight': style }
}
</script>

<style scoped>
.tablecell {
	color: var(--color-fg);
	background-color: var(--color-bg);
	text-align: center;
	font-size: var(--font-medium);
}

.tableheader {
	color: var(--color-menu);
	background-color: var(--color-bg);
	text-align: center;
	font-style: normal;
}
.heading {
	color: var(--color-battery);
}

.left {
	text-align: left;
}
</style>
