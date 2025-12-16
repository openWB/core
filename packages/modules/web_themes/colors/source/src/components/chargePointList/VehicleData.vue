<template>
	<div class="carTitleLine d-flex justify-content-between align-items-center">
		<h3 @click="changeCar = !changeCar">
			<i class="fa-solid fa-sm fa-car me-2" />
			{{ chargepoint.vehicleName }}
			<span
				v-if="visibleCars.length > 1"
				class="fa-solid fa-xs me-2"
				:class="changeCar ? 'fa-caret-up' : 'fa-caret-down'"
			/>
			<span
				v-if="chargepoint.hasPriority"
				class="me-1 fa-solid fa-xs fa-star ps-1"
			/>
			<span
				v-if="chargepoint.timedCharging"
				class="me-0 fa-solid fa-xs fa-clock ps-1"
			/>
		</h3>
		<WbBadge v-if="chargepoint.isSocConfigured" :bgcolor="batcolor">
			<BatterySymbol :soc="soc ?? 0" color="var(--color-bg)" class="me-2" />
			<i
				v-if="chargepoint.isSocManual"
				class="fa-solid fa-sm fas fa-edit"
				:style="{ color: 'var(--color-bg)' }"
				@click="editSoc = !editSoc"
			/>

			<i
				v-if="!chargepoint.isSocManual"
				type="button"
				class="fa-solid fa-sm"
				:class="chargepoint.waitingForSoc ? 'fa-spinner fa-spin' : 'fa-sync'"
				@click="loadSoc"
			/>
		</WbBadge>
	</div>
	<div v-if="changeCar" class="carSelector p-4 m-2">
		<span class="changeCarTitle mb-2">Fahrzeug wechseln:</span>
		<RadioInput2
			v-model.number="cp.connectedVehicle"
			:options="visibleCars.map((v) => [v.name, v.id])"
			@update:model-value="changeCar = false"
		/>
	</div>

	<div class="grid12">
		<!-- Chargemode buttons -->
		<RadioBarInput
			:id="'chargemode-' + chargepoint.name"
			v-model="chargeMode"
			class="chargemodes mt-3 mb-3"
			:options="
				Object.keys(chargemodes).map((v) => {
					return {
						text: chargemodes[v].name,
						value: v,
						color: chargemodes[v].color,
						icon: chargemodes[v].icon,
						active: chargemodes[v].mode == chargepoint.chargeMode,
					}
				})
			"
		/>
		<!-- Charging State -->
		<ChargingState
			v-if="chargepoint.power > 0"
			:chargepoint="chargepoint"
			:full-width="props.fullWidth"
		/>

		<InfoItem heading="letzte Ladung:" class="grid-col-4 grid-left">
			<FormatWattH
				:watt-h="Math.max(chargepoint.chargedSincePlugged, 0)"
			></FormatWattH>
		</InfoItem>
		<InfoItem heading="gel. Reichw.:" class="grid-col-4">
			{{ chargedRangeString }}
		</InfoItem>

		<InfoItem
			v-if="chargepoint.isSocConfigured"
			heading="Reichweite:"
			class="grid-col-4 grid-right"
		>
			{{
				vehicles[props.chargepoint.connectedVehicle]
					? Math.round(vehicles[props.chargepoint.connectedVehicle].range)
					: 0
			}}
			km
		</InfoItem>
		<div
			v-if="editSoc"
			class="socEditor rounded mt-2 d-flex flex-column align-items-center grid-col-12 grid-left"
		>
			<span class="d-flex m-1 p-0 socEditTitle">Ladestand einstellen:</span>
			<span class="d-flex justify-content-stretch align-items-center">
				<span>
					<RangeInput
						id="manualSoc"
						v-model="manualSoc"
						:min="0"
						:max="100"
						:step="1"
						unit="%"
					/>
				</span>
			</span>
			<span
				type="button"
				class="fa-solid d-flex fa-lg me-2 mb-3 align-self-end fa-circle-check"
				@click="setSoc"
			/>
		</div>
		<!-- ET Information -->
		<hr v-if="etData.active" class="divider grid-col-12" />

		<InfoItem
			v-if="etData.active"
			heading="Strompreis:"
			class="grid-col-4 grid-left"
		>
			<span :style="currentPriceStyle">{{ etData.etCurrentPriceString }} </span>
		</InfoItem>
		<InfoItem v-if="cp.etActive" heading="max. Preis:" class="grid-col-4">
			<span type="button" @click="editPrice = !editPrice"
				>{{
					props.chargepoint.etActive
						? (Math.round(props.chargepoint.etMaxPrice * 10) / 10).toFixed(1) +
							priceUnit
						: '-'
				}}
				<i
					v-if="props.chargepoint.etActive"
					class="fa-solid fa-sm fas fa-edit ms-2"
				/>
			</span>
		</InfoItem>

		<div
			v-if="editPrice"
			:id="'priceChartInline' + props.chargepoint.id"
			class="d-flex flex-column rounded priceEditor grid-col-12"
		>
			<PriceChart
				v-if="vehicles[props.chargepoint.connectedVehicle] != undefined"
				:chargepoint="props.chargepoint"
			/>
			<span
				class="d-flex ms-2 my-4 pe-3 pt-1 d-flex align-self-end"
				:style="modePillStyle"
				@click="editPrice = false"
			>
				<span
					type="button"
					class="d-flex fa-solid fa-lg ps-1 fa-circle-check"
				/>
			</span>
		</div>
	</div>
</template>

<script setup lang="ts">
import { computed, ref } from 'vue'
import { type ChargePoint, vehicles, chargePoints } from './model'
import { etData } from '../priceChart/model'
import { updateServer } from '@/assets/js/sendMessages'
import { chargemodes } from '@/assets/js/themeConfig'
import BatterySymbol from '@/components/shared/BatterySymbol.vue'
import FormatWattH from '../shared/FormatWattH.vue'
import RadioBarInput from '@/components/shared/RadioBarInput.vue'
import RadioInput2 from '@/components/shared/RadioInput2.vue'
import WbBadge from '../shared/WbBadge.vue'
import RangeInput from '../shared/RangeInput.vue'
import PriceChart from '../priceChart/PriceChart.vue'
import InfoItem from '@/components/shared/InfoItem.vue'
import ChargingState from './ChargingState.vue'
import { globalData } from '@/assets/js/model'

const props = defineProps<{
	chargepoint: ChargePoint
	fullWidth?: boolean
}>()
const cp = props.chargepoint
const editSoc = ref(false)
const editPrice = ref(false)
const changeCar = ref(false)

// computed
const chargeMode = computed({
	get() {
		return cp.chargeMode
	},
	set(newMode) {
		cp.chargeMode = newMode
	},
})
const chargedRangeString = computed(() => {
	const rangeSincePlugged = props.chargepoint.rangeCharged
	const energySincePlugged = props.chargepoint.chargedSincePlugged
	const energyToday = props.chargepoint.dailyYield
	if (energySincePlugged > 0) {
		return (
			Math.round(
				(rangeSincePlugged / energySincePlugged) * energyToday,
			).toString() +
			' ' +
			props.chargepoint.rangeUnit
		)
	} else {
		return '0 km'
	}
})
const soc = computed(() => {
	return props.chargepoint.soc
})
const manualSoc = computed({
	get() {
		return props.chargepoint.soc
	},
	set(s: number) {
		chargePoints[props.chargepoint.id].soc = s
	},
})

const currentPrice = computed(() => {
	const [p] = etData.etPriceList.values()
	return (Math.round(p * 10) / 10).toFixed(1)
})
const currentPriceStyle = computed(() => {
	return props.chargepoint.etMaxPrice >= +currentPrice.value
		? { color: 'var(--color-charging)' }
		: { color: 'var(--color-menu)' }
})
const visibleCars = computed(() => {
	return Object.values(vehicles).filter((v) => v.visible)
})
const batcolor = computed(() => {
	if (props.chargepoint.soc < 20) {
		return 'var(--color-evu)'
	} else if (props.chargepoint.soc >= 80) {
		return 'var(--color-pv)'
	} else {
		return 'var(--color-battery)'
	}
})
const modePillStyle = computed(() => {
	switch (props.chargepoint.chargeMode) {
		case 'stop':
			return { color: 'var(--fg)' }
		default:
			return {
				color: chargemodes[props.chargepoint.chargeMode].color,
			}
	}
})
const priceUnit = computed(() => {
	return globalData.country === 'ch' ? ' Rp' : ' ct'
})
//methods
function loadSoc() {
	updateServer('socUpdate', 1, props.chargepoint.connectedVehicle)
	chargePoints[props.chargepoint.id].waitingForSoc = true
}
function setSoc() {
	updateServer('setSoc', manualSoc.value, props.chargepoint.connectedVehicle)
	editSoc.value = false
}
</script>
<style scoped>
.fa-star {
	color: var(--color-evu);
}
.fa-clock {
	color: var(--color-charging);
}
.fa-car {
	color: var(--color-menu);
}
.fa-circle-check {
	color: var(--color-menu);
}
.socEditor {
	border: 1px solid var(--color-menu);
	justify-self: stretch;
}
.priceEditor {
	border: 1px solid var(--color-menu);
	justify-self: stretch;
}
.chargemodes {
	grid-column: 1 / 13;
	justify-self: center;
}
.chargeinfo {
	display: grid;
	grid-template-columns: repeat(12, auto);
	justify-content: space-between;
}
.divider {
	border-top: 1px solid var(--color-fg);
	width: 100%;
}
.carSelector {
	border: 1px solid var(--color-menu);
	font-size: var(--font-settings);
	border-radius: 3px;
	display: flex;
	flex-direction: column;
}
</style>
