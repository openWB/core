<template>
	<div class="container-fluid p-0 m-0">
		<ConfigItem title="Ladestand" :fullwidth="true">
			<RangeInput
				id="soc"
				v-model="plan.soc"
				:min="0"
				:max="100"
				:step="1"
				unit="%"
			/>
		</ConfigItem>
		<ConfigItem title="Zielzeit beachten" :fullwidth="true">
			<SwitchInput v-model="plan.timed" />
		</ConfigItem>
		<ConfigItem title="Uhrzeit" :fullwidth="true">
			<TimeInput v-model="plan.time" />
		</ConfigItem>
		<ConfigItem title="Wiederholungen" :fullwidth="true">
			<SelectInput v-model="plan.frequency.selected" :options="frequencies" />
		</ConfigItem>
		<ConfigItem
			v-if="plan.frequency.selected == 'once'"
			title="Gültig ab"
			:fullwidth="true"
		>
			<DateInput v-model="plan.frequency.once[0]" />
		</ConfigItem>
		<ConfigItem
			v-if="plan.frequency.selected == 'once'"
			title="Gültig bis"
			:fullwidth="true"
		>
			<DateInput v-model="plan.frequency.once[1]" />
		</ConfigItem>
		<ConfigItem
			v-if="plan.frequency.selected == 'weekly'"
			title="Wochentage"
			:fullwidth="true"
		>
			<CheckBoxInput v-model="plan.frequency.weekly" :options="days" />
		</ConfigItem>
		<div class="row mt-2">
			<div class="col d-flex justify-content-end">
				<button
					class="btn btn-danger"
					data-bs-dismiss="modal"
					@click="$emit('deletePlan', planId)"
				>
					Löschen
				</button>
				<button
					class="btn btn-warning ms-1"
					data-bs-dismiss="modal"
					@click="$emit('abort')"
				>
					Abbrechen
				</button>
				<button
					class="btn btn-success float-end ms-1"
					data-bs-dismiss="modal"
					@click="$emit('savePlan', planId)"
				>
					Speichern
				</button>
			</div>
		</div>
	</div>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import { chargeTemplates, createChargeSchedule } from '../model'
import ConfigItem from '../../shared/ConfigItem.vue'
import RangeInput from '@/components/shared/RangeInput.vue'
import SelectInput from '@/components/shared/SelectInput.vue'
import CheckBoxInput from '@/components/shared/CheckBoxInput.vue'
import TimeInput from '@/components/shared/TimeInput.vue'
import DateInput from '@/components/shared/DateInput.vue'
import SwitchInput from '../../shared/SwitchInput.vue'
const props = defineProps<{
	chargeTemplateId: number
	planId: string
}>()
defineEmits(['deletePlan', 'abort', 'savePlan'])

const frequencies: [string | number, string | number][] = [
	['Einmalig', 'once'],
	['Täglich', 'daily'],
	['Wöchentlich', 'weekly'],
]
const days = [
	'Montag',
	'Dienstag',
	'Mittwoch',
	'Donnerstag',
	'Freitag',
	'Samstag',
	'Sonntag',
]
const template = computed(() => {
	return chargeTemplates[props.chargeTemplateId]
})
const plan = computed(() => {
	let p = template.value.chargemode.scheduled_charging.plans[props.planId]
	if (p) {
		return p
	} else {
		return createChargeSchedule() // create a dummy time plan in case the list of plans in the template is empty
	}
})
</script>

<style scoped>
.time-input {
	background-color: var(--color-bg);
	color: var(--color-fg);
	border: 1px solid var(--color-menu);
}
</style>
