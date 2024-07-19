<template>
	<p class="heading ms-1 pt-2">Zeitpläne:</p>
	<table class="table table-borderless">
		<thead>
			<tr>
				<th class="tableheader">Von</th>
				<th class="tableheader">Bis</th>
				<th class="tableheader">Ladestrom</th>
				<th class="tableheader">Wiederholung</th>
				<th class="tableheader right" />
			</tr>
		</thead>
		<tbody>
			<tr v-for="(plan, i) in plans" :key="i" :style="cellStyle(i)">
				<td class="tablecell">
					{{ plan.time[0] }}
				</td>
				<td class="tablecell">
					{{ plan.time[1] }}
				</td>
				<td class="tablecell">{{ plan.current }} A</td>
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
import { timeChargingPlans } from '../model'

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
.right {
	text-align: right;
}
</style>
