<template>
	<div class="plandetails d-flex flex-cloumn">
		<hr />
		<span class="heading">Details für {{ props.plan.name }}:</span>
		<ul>
			<li>{{ targetString }}</li>
			<li>{{ repeatString }}</li>
			<li v-if="props.plan.et_active">Preisbasiert laden</li>
		</ul>
		<button class="btn btn-outline-secondary btn-sm" @click="$emit('close')">
			Ok
		</button>
	</div>
</template>
<script setup lang="ts">
import { computed } from 'vue'
import { type ChargeSchedule } from '../model'
import { formatWattH } from '@/assets/js/helpers'
const props = defineProps<{
	plan: ChargeSchedule
}>()
defineEmits(['close'])
const targetString = computed(() => {
	if (props.plan.limit.selected == 'soc') {
		return `Lade bis ${props.plan.time} auf ${props.plan.limit.soc_scheduled}% (maximal ${props.plan.limit.soc_limit}% mit PV)`
	} else if (props.plan.limit.selected == 'amount') {
		return `Energiemenge: ${formatWattH(props.plan.limit.amount)}`
	} else {
		return 'Keine Begrenzung'
	}
})
const repeatString = computed(() => {
	let result = `Wiederholung `

	switch (props.plan.frequency.selected) {
		case 'daily':
			result += 'täglich'
			break
		case 'once':
			result += `einmal (${props.plan.frequency.once})`
			break
		case 'weekly':
			result += 'wöchentlich ' + weekDayString.value
			break
		default:
			result += 'unbekannt'
	}
	return result
})
const weekDayString = computed(() => {
	const days = [
		'Montag',
		'Dienstag',
		'Mittwoch',
		'Donnerstag',
		'Freitag',
		'Samstag',
		'Sonntag',
	]
	let result = '('
	props.plan.frequency.weekly.forEach((day, index) => {
		if (day) {
			result += `${days[index]} `
		}
	})
	result = result.trim()
	result += ')'
	return result
})
</script>
<style scoped>
.heading {
	font-size: var(--font-settings);
	color: var(--color-charging);
	font-weight: bold;
	margin-bottom: 0.5rem;
}
.plandetails {
	display: flex;
	flex-direction: column;
}
</style>
