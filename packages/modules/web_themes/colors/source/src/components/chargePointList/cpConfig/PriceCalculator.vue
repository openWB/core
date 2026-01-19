<template>
	<ModalComponent :modal-id="'priceCalculator-' + cpId">
		<template #title> Maximaler Strompreis für {{ cp.vehicleName }} </template>
		<template #footer>
			<button
				class="closebutton btn btn-secondary"
				@click="$emit('update:modelValue', maxPrice)"
			>
				Preis bestätigen
			</button>
		</template>
		<div class="pricecalculator p-2">
			<InfoItem class="infoitem" heading="Aktueller SoC"
				>{{ currentSoc }}%
			</InfoItem>
			<InfoItem class="infoitem" heading="Batterie-Kapazität"
				>{{ (evTemplate.battery_capacity ?? 0) / 1000 }} kWh
			</InfoItem>
			<InfoItem class="infoitem" heading="Ladestrom">
				{{ evTemplate.max_current_multi_phases ?? 0 }} A
			</InfoItem>
			<ConfigItem2
				title="Ziel-SoC"
				icon="fa-battery-full"
				:fullwidth="true"
				:infotext="`Der gewünschte Ladezustand, der bis zur Zielzeit erreicht sein soll. Aktueller SoC: ${currentSoc}%`"
			>
				<RangeInput
					id="targetSoc"
					v-model="targetSoc"
					:min="currentSoc"
					:max="100"
					:step="1"
					unit="%"
				/>
			</ConfigItem2>
			<ConfigItem2
				title="Zielzeit"
				icon="fa-clock"
				:fullwidth="true"
				:infotext="`Die Uhrzeit, zu der das Fahrzeug auf dem angegebenen Ladestand sein soll.`"
			>
				<DateRangeInput
					id="targetTime"
					v-model="newTime"
					:min="new Date()"
					:max="etData.maxDate() ?? new Date()"
					:step="900000"
					unit="min"
				/>
			</ConfigItem2>
			<ConfigItem2
				title="Ladezeit-Puffer"
				icon="fa-clock"
				:fullwidth="true"
				:infotext="`Der zeitliche Puffer, der zur berechneten Ladezeit hinzugerechnet wird. Dadurch wird sichergestellt, dass das Fahrzeug rechtzeitig fertig geladen ist.`"
			>
				<RangeInput
					id="bufferMinutes"
					v-model="bufferMinutes"
					:min="0"
					:max="60"
					:step="1"
					unit="min"
				/>
			</ConfigItem2>
			<InfoItem class="infoitem" heading="Ladezeit"
				>{{ Math.floor((chargeDuration + bufferMinutes) / 60) }}h
				{{ Math.round((chargeDuration + bufferMinutes) % 60) }}min
			</InfoItem>
			<InfoItem class="infoitem" heading="Höchstpreis"
				><span class="targetprice" :style="targetPriceStyle">{{
					targetPrice
				}}</span>
			</InfoItem>
		</div>
	</ModalComponent>
</template>
<script setup lang="ts">
import { computed, ref } from 'vue'
import ModalComponent from '@/components/shared/ModalComponent.vue'
import InfoItem from '@/components/shared/InfoItem.vue'
import ConfigItem2 from '@/components/shared/ConfigItem2.vue'
import RangeInput from '@/components/shared/RangeInput.vue'
import DateRangeInput from '@/components/shared/DateRangeInput.vue'
import { chargePoints, evTemplates, chargeTemplates } from '../model'
import { etData } from '@/components/priceChart/model'
import { globalData } from '@/assets/js/model'
const props = defineProps<{
	modelValue: number
	cpId: number
}>()
const emit = defineEmits(['update:modelValue', 'deletePlan'])
const cp = computed(() => chargePoints[props.cpId])
const currentSoc = cp.value.soc
var targetSoc = ref(80)
const bufferMinutes = ref(30)
const evTemplate = computed(() => evTemplates[cp.value.evTemplate])
const chargeTemplate = computed(() => chargeTemplates[cp.value.evTemplate])

const price = computed({
	get() {
		return props.modelValue
	},
	set(value: number) {
		emit('update:modelValue', value)
	},
})
const newTime = ref(etData.maxDate() ?? new Date())
const chargeDuration = computed(() => {
	if (evTemplate.value != null) {
		const batteryCapacity = evTemplate.value.battery_capacity ?? 0 //in Wh
		const phases = Math.min(
			evTemplate.value.max_phases,
			chargeTemplate.value.chargemode.eco_charging.phases_to_use,
		)
		const chargingPower =
			evTemplate.value.max_current_multi_phases * phases * 230
		const neededCapacity =
			(batteryCapacity * (targetSoc.value - currentSoc)) / 100
		return (neededCapacity / chargingPower) * 60 //in minutes
	} else {
		return -1
	}
})
const maxPrice = computed(() => {
	return etData.maxPriceForDuration(
		chargeDuration.value + bufferMinutes.value,
		newTime.value,
	)
})

const targetPrice = computed(() => {
	if (maxPrice.value > 0) {
		return `${Math.round(maxPrice.value * 100) / 100} ${globalData.country == 'ch' ? 'Rp' : 'ct'}`
	} else {
		return 'Ziel nicht erreichbar'
	}
})
const targetPriceStyle = computed(() => {
	if (maxPrice.value > price.value) {
		return 'color: var(--color-charging);'
	} else {
		return 'color: var(--color-evu);'
	}
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
.pricecalculator {
	display: grid;
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
.infoitem {
	grid-column: span 4;
}
.targetprice {
	color: var(--color-charging);
}
</style>
