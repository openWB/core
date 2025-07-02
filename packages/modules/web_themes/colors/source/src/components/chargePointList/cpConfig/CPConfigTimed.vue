<template>
	<ConfigItem title="Zeitplan aktiv" icon="fa-clock" :fullwidth="true">
		<template #inline-item>
			<SwitchInput v-model="cp.timedCharging" />
		</template>
	</ConfigItem>
	<p class="heading ms-1 pt-2">Zeitpläne:</p>
	<table class="table table-borderless">
		<thead>
			<tr>
				<th class="tableheader left" />
				<th class="tableheader">Von</th>
				<th class="tableheader">Bis</th>
				<th class="tableheader">Strom</th>
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
					<span
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
					></span>
				</td>
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
				<td class="tablecell right">
					<i
						class="me-1 fa-solid fa-sm fa-circle-info"
						@click="showPlanDetails = !showPlanDetails"
					/>
				</td>
			</tr>
		</tbody>
	</table>

	<div v-if="showPlanDetails">
		<TimePlanDetails
			v-for="plan in plans"
			:key="plan.id"
			:plan="plan"
			@close="showPlanDetails = false"
		/>
	</div>
</template>

<script setup lang="ts">
import { computed, ref } from 'vue'
import { ChargePoint, type ChargeTimePlan } from '../model'
import { updateChargeTemplate } from '@/assets/js/sendMessages'
import TimePlanDetails from './TimePlanDetails.vue'
import SwitchInput from '@/components/shared/SwitchInput.vue'
import ConfigItem from '../../shared/ConfigItem.vue'
const props = defineProps<{
	chargePoint: ChargePoint
}>()

const showPlanDetails = ref(false)
const cp = props.chargePoint
const freqNames: { [key: string]: string } = {
	daily: 'Täglich',
	once: 'Einmal',
	weekly: 'Woche',
}

const plans = computed(
	() =>
		props.chargePoint?.chargeTemplate?.time_charging.plans ??
		([] as ChargeTimePlan[]),
)

function switchStyle(key: number) {
	const style = plans.value[key].active
		? 'var(--color-switchGreen)'
		: 'var(--color-switchRed)'
	return { color: style }
}
function toggleSwitch(i: number) {
	props.chargePoint.chargeTemplate!.time_charging.plans[i]!.active =
		!plans.value[i].active
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
</style>
