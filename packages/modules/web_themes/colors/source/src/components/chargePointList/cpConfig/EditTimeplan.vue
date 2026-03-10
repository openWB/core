<template>
	<ModalComponent :modal-id="'timePlanSettings-' + cpId + '-' + modelValue.id">
		<template #title> Einstellungen Zeitladen: {{ modelValue.name }} </template>
		<template #footer>
			<button
				class="closebutton btn btn-secondary"
				@click="$emit('update:modelValue', plan)"
			>
				Speichern
			</button>
		</template>
		<div class="planeditor p-2">
			<ConfigItem2 title="Name" icon="fa-calendar-check" :fullwidth="true">
				<template #inline-item>
					<TextInput v-model="plan.name" :text="'Name des Plans'" />
				</template>
			</ConfigItem2>
			<ConfigItem2 title="Aktiv" icon="fa-power-off" :fullwidth="true">
				<template #inline-item>
					<SwitchInput v-model="plan.active" />
				</template>
			</ConfigItem2>
			<ConfigItem2 title="Ladebeginn" icon="fa-clock" :fullwidth="true">
				<template #inline-item>
					<TimeInput v-model="plan.time[0]" :text="'Startzeit (HH:MM)'" />
				</template>
			</ConfigItem2>
			<ConfigItem2 title="Ladeende" icon="fa-clock" :fullwidth="true">
				<template #inline-item>
					<TimeInput v-model="plan.time[1]" :text="'Zielzeit (HH:MM)'" />
				</template>
			</ConfigItem2>
			<ConfigItem2 title="Ladestrom" icon="fa-bolt" :fullwidth="true">
				<RangeInput
					id="chargeCurrent"
					v-model="plan.current"
					:min="6"
					:max="32"
					:step="1"
					unit="A"
				/>
			</ConfigItem2>
			<ConfigItem2 title="Begrenzung" icon="fa-bullseye" :fullwidth="true">
				<template #inline-item>
					<RadioInput
						v-model="plan.limit.selected"
						:options="[
							['Aus', 'none'],
							['Soc', 'soc'],
							['Energie', 'amount'],
						]"
					/>
				</template>
			</ConfigItem2>
			<ConfigItem2
				v-if="plan.limit.selected === 'soc'"
				title="Ziel-SoC für das Fahrzeug"
				icon="fa-battery-half"
				:fullwidth="true"
			>
				<RangeInput
					id="evSoc"
					v-model="plan.limit.soc!"
					:min="0"
					:max="100"
					:step="1"
					unit="%"
				/>
			</ConfigItem2>
			<ConfigItem2
				v-if="plan.limit.selected === 'amount'"
				title="Ziel-Energie"
				icon="fa-charging-station"
				:fullwidth="true"
			>
				<RangeInput
					id="energyAmount"
					v-model="energy"
					:min="1"
					:max="150"
					:step="1"
					unit="kWh"
				/>
			</ConfigItem2>
			<ConfigItem2 title="Wiederholungen" icon="fa-repeat" :fullwidth="true">
				<RadioInput2
					v-model="plan.frequency.selected"
					:options="[
						['Einmalig', 'once'],
						['Täglich', 'daily'],
						['Wöchentlich', 'weekly'],
					]"
				/>
			</ConfigItem2>
			<ConfigItem2 v-if="plan.frequency.selected === 'once'" title="Gültig ab">
				<template #inline-item>
					<DateInput2
						v-model="startDate"
						:input-id="
							'time-from-date-' + props.cpId.toString() + '-' + plan.id
						"
					/>
				</template>
			</ConfigItem2>
			<ConfigItem2 v-if="plan.frequency.selected === 'once'" title="Gültig bis">
				<template #inline-item>
					<DateInput2
						v-model="endDate"
						:input-id="'time-to-date-' + props.cpId.toString() + '-' + plan.id"
					/>
				</template>
			</ConfigItem2>
			<ConfigItem2 v-if="plan.frequency.selected === 'weekly'" title="Tage">
				<CheckBoxInput
					v-model="plan.frequency.weekly"
					:options="['Mo', 'Di', 'Mi', 'Do', 'Fr', 'Sa', 'So']"
				/>
			</ConfigItem2>
			<ConfigItem2 title="Anzahl Phasen" icon="fa-plug" :fullwidth="true">
				<RadioInput2
					v-model="plan.phases_to_use"
					:options="[
						['1', 1],
						['Maximum', 3],
					]"
				/>
			</ConfigItem2>
			<button
				class="btn delete_button align-self-center"
				type="button"
				@click="$emit('deletePlan', plan)"
			>
				Plan löschen
			</button>
		</div>
	</ModalComponent>
</template>
<script setup lang="ts">
import { computed } from 'vue'
import { type ChargeTimePlan } from '../model'
import ModalComponent from '@/components/shared/ModalComponent.vue'
import ConfigItem2 from '@/components/shared/ConfigItem2.vue'
import TextInput from '@/components/shared/TextInput.vue'
import SwitchInput from '@/components/shared/SwitchInput.vue'
import RangeInput from '@/components/shared/RangeInput.vue'
import RadioInput from '@/components/shared/RadioInput.vue'
import RadioInput2 from '@/components/shared/RadioInput2.vue'
import DateInput2 from '@/components/shared/DateInput2.vue'
import CheckBoxInput from '@/components/shared/CheckBoxInput.vue'
import TimeInput from '@/components/shared/TimeInput.vue'
const props = defineProps<{
	modelValue: ChargeTimePlan
	cpId: number
}>()
const emit = defineEmits(['update:modelValue', 'deletePlan'])
const plan = computed({
	get() {
		return props.modelValue
	},
	set(value: number | string) {
		emit('update:modelValue', value)
	},
})
const energy = computed({
	get() {
		return plan.value.limit.amount! / 1000
	},
	set(value: number) {
		plan.value.limit.amount = value * 1000
	},
})
const startDate = computed({
	get() {
		return new Date(plan.value.frequency.once![0])
	},
	set(value: Date) {
		plan.value.frequency.once![0] = `${value.getFullYear()}-${value.getMonth() + 1}-${value.getDate()}`
	},
})
const endDate = computed({
	get() {
		return new Date(plan.value.frequency.once![1])
	},
	set(value: Date) {
		plan.value.frequency.once![1] = `${value.getFullYear()}-${value.getMonth() + 1}-${value.getDate()}`
	},
})
</script>
<style scoped>
.heading {
	font-size: var(--font-settings);
	color: var(--color-charging);
	font-weight: bold;
	margin-bottom: 0.5rem;
}
.configheader {
	font-size: var(--font-settings);
	color: var(--color-charging);
	font-weight: bold;
	margin-bottom: 1rem;
	text-align: center;
}
.planeditor {
	display: grid;
	grid-template-columns: repeat(2, auto);
}
.closebutton {
	font-size: var(--font-settings);
	background-color: var(--color-charging);
	color: white;
}
.delete_button {
	grid-column: span 12;
	font-size: var(--font-settings);
	color: var(--color-evu);
	text-align: center;
}
</style>
