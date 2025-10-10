<template>
	<p class="heading ms-1 pt-2">Pläne für Zielladen:</p>
	<table v-if="plans.length > 0" class="table table-borderless">
		<thead>
			<tr>
				<th class="tableheader left" />
				<th class="tableheader left">Plan</th>
				<th class="tableheader">Zeit</th>
				<th class="tableheader">Ziel</th>
				<th class="tableheader">Wiederh.</th>

				<th class="tableheader right" />
			</tr>
		</thead>
		<tbody>
			<tr
				v-for="(plan, i) in plans"
				:key="i"
				:class="plan.active ? 'text-bold' : 'text-normal'"
			>
				<td class="tablecell left">
					<a
						v-if="props.chargePoint.chargeTemplate?.id != undefined"
						@click="toggleSwitch(i)"
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
				<td class="tablecell left">{{ plan.name }}</td>
				<td class="tablecell">
					{{ timeString(i) }}
				</td>
				<td class="tablecell">
					{{
						plan.limit.selected == 'soc'
							? plan.limit.soc_scheduled + '%'
							: formatWattH(plan.limit.amount, 0)
					}}
				</td>
				<td class="tablecell">
					{{ freqNames[plan.frequency.selected] }}
				</td>

				<td class="tablecell right">
					<i
						class="me-1 fa-solid fa-sm fa-circle-info"
						@click="showPlanDetails = !showPlanDetails"
					/>
				</td>
			</tr>
		</tbody>
	</table>
	<p v-else class="ms-1">
		Pläne für das Zielladen können in den Einstellungen des Ladeprofils angelegt
		werden .
	</p>

	<div v-if="showPlanDetails">
		<ScheduleDetails
			v-for="plan in plans"
			:key="plan.id"
			:plan="plan"
			@close="showPlanDetails = false"
		/>
	</div>
</template>

<script setup lang="ts">
import { computed, ref } from 'vue'
import { ChargePoint, type ChargeSchedule } from '../model'
import { updateChargeTemplate } from '@/assets/js/sendMessages'
import ScheduleDetails from './ScheduleDetails.vue'
import { formatWattH } from '@/assets/js/helpers'

const showPlanDetails = ref(false)
const freqNames: { [key: string]: string } = {
	daily: 'Täglich',
	once: 'Einmal',
	weekly: 'Woche',
}
const props = defineProps<{
	chargePoint: ChargePoint
}>()

//computed
const plans = computed(
	() =>
		props.chargePoint?.chargeTemplate?.chargemode.scheduled_charging.plans ??
		([] as ChargeSchedule[]),
)
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
function toggleSwitch(i: number) {
	props.chargePoint.chargeTemplate!.chargemode.scheduled_charging.plans[
		i
	]!.active = !plans.value[i].active
	updateChargeTemplate(props.chargePoint.id)
}
</script>

<style scoped>
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
</style>
