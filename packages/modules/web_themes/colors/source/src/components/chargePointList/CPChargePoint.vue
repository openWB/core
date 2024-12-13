<template>
	<WBWidget
		v-if="!configmode"
		:variable-width="true"
		:full-width="props.fullWidth"
	>
		<template #title>
			<span class="d-flex justify-content-center align-items-center">
				<span :style="cpNameStyle" @click="configmode = !configmode">
					<span class="fa-solid fa-charging-station">&nbsp;</span>
					{{ props.chargepoint.name }}</span
				>
				<span
					v-if="cp.faultState == 2"
					class="WbBadge rounded-pill errorWbBadge ms-3"
					>Fehler</span
				>
			</span>
		</template>

		<template #buttons>
			<span
				type="button"
				class="ms-2 ps-1 pt-1"
				:style="modePillStyle"
				@click="configmode = !configmode"
			>
				<span class="fa-solid fa-lg ps-1 fa-ellipsis-vertical" />
			</span>
		</template>

		<!-- Chargepoint info -->
		<div v-if="!configmode">
			<div class="grid12" @click="configmode = !configmode">
				<!-- Status information -->
				<InfoItem heading="Status:" class="grid-col-4 grid-left">
					<span :style="{ color: statusColor }">
						<i :class="statusIcon" />
						{{ statusString }}
					</span>
				</InfoItem>
				<!-- Ladung -->
				<InfoItem heading="Geladen:" class="grid-col-4 grid-left">
					<FormatWattH :watt-h="chargepoint.dailyYield" />
				</InfoItem>
			</div>
		</div>
		<div v-if="configmode" class="row m-0 mt-0 p-0">
			<div class="col m-0 p-0">
				<CPChargeConfigPanel
					v-if="chargepoint != undefined"
					:chargepoint="chargepoint"
				/>
			</div>
		</div>
		<!-- Car information-->
		<template #footer>
			<div v-if="!configmode">
				<div class="row">
					<div class="col">
						<div
							class="carTitleLine d-flex justify-content-between align-items-center"
						>
							<h3 @click="configmode = !configmode">
								<i class="fa-solid fa-sm fa-car me-2" />
								{{ chargepoint.vehicleName }}
								<span
									v-if="chargepoint.hasPriority"
									class="me-1 fa-solid fa-xs fa-star ps-1"
								/>
								<span
									v-if="chargepoint.etActive"
									class="me-1 fa-solid fa-xs fa-coins ps-0"
								/>
								<span
									v-if="chargepoint.timedCharging"
									class="me-0 fa-solid fa-xs fa-clock ps-1"
								/>
							</h3>
							<WbBadge v-if="chargepoint.isSocConfigured" :bgcolor="batcolor">
								<BatterySymbol
									:soc="soc ?? 0"
									color="var(--color-bg)"
									class="me-2"
								/>
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
									:class="
										chargepoint.waitingForSoc ? 'fa-spinner fa-spin' : 'fa-sync'
									"
									@click="loadSoc"
								/>
							</WbBadge>
						</div>
					</div>
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
					<!-- Car info -->
					<!-- Leistung -->
					<InfoItem
						v-if="props.chargepoint.power > 0"
						heading="Leistung:"
						class="grid-col-3 grid-left mb-3"
					>
						<span style="color: var(--color-charging)">
							<FormatWatt :watt="props.chargepoint.power" /> </span
					></InfoItem>
					<InfoItem
						v-if="props.chargepoint.power > 0"
						heading="Strom:"
						class="grid-col-3"
					>
						<span style="color: var(--color-charging)">
							{{ realChargeAmpereString }}
						</span>
					</InfoItem>
					<InfoItem
						v-if="props.chargepoint.power > 0"
						heading="Phasen:"
						class="grid-col-3"
					>
						<span style="color: var(--color-charging)">
							{{ props.chargepoint.phasesInUse }}
						</span>
					</InfoItem>
					<InfoItem
						v-if="props.chargepoint.power > 0"
						heading="Sollstrom:"
						class="grid-col-3 grid-right"
					>
						<span class="targetCurrent">{{ chargeAmpereString }}</span>
					</InfoItem>

					<!-- Ladung -->
					<!-- <InfoItem heading="Geladen:" class="grid-col-4 grid-left">
						<FormatWattH :watt-h="chargepoint.dailyYield" />
					</InfoItem>
					 --><!-- geladene Reichweite-->
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
					<!-- <InfoItem heading="Zeitplan:" class="grid-col-4 grid-right">
						<span v-if="chargepoint.timedCharging" class="me-1 fa-solid fa-xs fa-clock ps-1" />
						{{ props.chargepoint.timedCharging ? 'Ja' : 'Nein' }}
					</InfoItem> -->

					<div
						v-if="editSoc"
						class="socEditor rounded mt-2 d-flex flex-column align-items-center grid-col-12 grid-left"
					>
						<span class="d-flex m-1 p-0 socEditTitle"
							>Ladestand einstellen:</span
						>
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
					<hr class="divider grid-col-12" />
					<InfoItem
						v-if="etData.active"
						heading="Preisladen:"
						class="grid-col-4 grid-left"
					>
						<SwitchInput v-model="cp.etActive" />
					</InfoItem>
					<InfoItem
						v-if="etData.active"
						heading="max. Preis:"
						class="grid-col-4"
					>
						<span type="button" @click="editPrice = !editPrice"
							>{{
								props.chargepoint.etActive
									? (
											Math.round(props.chargepoint.etMaxPrice * 10) / 10
										).toFixed(1) + ' ct'
									: '-'
							}}

							<i
								v-if="props.chargepoint.etActive"
								class="fa-solid fa-sm fas fa-edit ms-2"
							/>
						</span>
					</InfoItem>
					<InfoItem
						v-if="etData.active"
						heading="akt. Preis:"
						class="grid-col-4 grid-right"
					>
						<span :style="currentPriceStyle">{{ currentPrice }} ct </span>
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
			</div>
		</template>
	</WBWidget>
	<WbWidgetFlex v-if="configmode" :full-width="props.fullWidth">
		<template #title>
			<span :style="cpNameStyle" @click="configmode = !configmode">
				<span class="fas fa-gear">&nbsp;</span>
				Einstellungen {{ props.chargepoint.name }}</span
			>
		</template>

		<template #buttons>
			<span
				class="ms-2 pt-1"
				:style="modePillStyle"
				@click="configmode = !configmode"
			>
				<span class="fa-solid fa-lg ps-1 fa-circle-check" />
			</span>
		</template>
		<CPChargeConfigPanel
			v-if="chargepoint != undefined"
			:chargepoint="chargepoint"
		/>
	</WbWidgetFlex>
</template>

<script setup lang="ts">
import { computed, ref } from 'vue'
import { type ChargePoint, vehicles, chargePoints } from './model'
import { chargemodes } from '@/assets/js/themeConfig'
import WBWidget from '@/components/shared/WBWidget.vue'
import InfoItem from '@/components/shared/InfoItem.vue'
import CPChargeConfigPanel from './cpConfig/CPChargeConfigPanel.vue'
import BatterySymbol from '@/components/shared/BatterySymbol.vue'
import FormatWatt from '@/components/shared/FormatWatt.vue'
import FormatWattH from '../shared/FormatWattH.vue'
import RadioBarInput from '@/components/shared/RadioBarInput.vue'
import WbWidgetFlex from '../shared/WbWidgetFlex.vue'
import WbBadge from '../shared/WbBadge.vue'
import { updateServer } from '@/assets/js/sendMessages'
import RangeInput from '../shared/RangeInput.vue'
import PriceChart from '../priceChart/PriceChart.vue'
import { etData } from '../priceChart/model'
import SwitchInput from '../shared/SwitchInput.vue'

const props = defineProps<{
	chargepoint: ChargePoint
	fullWidth?: boolean
}>()
const cp = ref(props.chargepoint)
// computed
const chargeMode = computed({
	get() {
		return props.chargepoint.chargeMode
	},
	set(newMode) {
		chargePoints[props.chargepoint.id].chargeMode = newMode
	},
})
const chargeAmpereString = computed(() => {
	return (
		(Math.round(props.chargepoint.current * 10) / 10).toLocaleString(
			undefined,
		) + ' A'
	)
})
const realChargeAmpereString = computed(() => {
	return (
		(Math.round(props.chargepoint.realCurrent * 10) / 10).toLocaleString(
			undefined,
		) + ' A'
	)
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
const statusString = computed(() => {
	if (props.chargepoint.isLocked) {
		return 'Gesperrt'
	} else if (props.chargepoint.isCharging) {
		return 'Lädt'
	} else if (props.chargepoint.isPluggedIn) {
		return 'Bereit'
	} else {
		return 'Frei'
	}
})
const statusColor = computed(() => {
	if (props.chargepoint.isLocked) {
		return 'var(--color-evu)'
	} else if (props.chargepoint.isCharging) {
		return 'var(--color-charging)'
	} else if (props.chargepoint.isPluggedIn) {
		return 'var(--color-battery)'
	} else {
		return 'var(--color-axis)'
	}
})
const statusIcon = computed(() => {
	let icon = ''
	if (props.chargepoint.isLocked) {
		icon = 'fa-lock'
	} else if (props.chargepoint.isCharging) {
		icon = ' fa-bolt'
	} else if (props.chargepoint.isPluggedIn) {
		icon = 'fa-plug'
	}
	return 'fa ' + icon
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
const soc = computed(() => {
	return props.chargepoint.soc
})
const cpNameStyle = computed(() => {
	return { color: props.chargepoint.color }
	// return { color: 'var(--color-fg)' }
})
const currentPriceStyle = computed(() => {
	return props.chargepoint.etMaxPrice >= +currentPrice.value
		? { color: 'var(--color-charging)' }
		: { color: 'var(--color-menu)' }
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
const configmode = ref(false)
const editSoc = ref(false)
function loadSoc() {
	updateServer('socUpdate', 1, props.chargepoint.connectedVehicle)
	chargePoints[props.chargepoint.id].waitingForSoc = true
}
function setSoc() {
	updateServer('setSoc', manualSoc.value, props.chargepoint.connectedVehicle)
	editSoc.value = false
}
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
const editPrice = ref(false)
// methods
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

.fa-ellipsis-vertical {
	color: var(--color-menu);
}

.fa-circle-check {
	color: var(--color-menu);
}

.fa-coins {
	color: var(--color-battery);
}

.socEditor {
	border: 1px solid var(--color-menu);
	justify-self: stretch;
}

.targetCurrent {
	color: var(--color-menu);
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

.errorWbBadge {
	color: var(--color-bg);
	background-color: var(--color-evu);
	font-size: var(--font-small);
}

.divider {
	color: var(--color-fg);
}

.blue {
	color: var(--color-charging);
}
</style>
