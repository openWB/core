<template>
	<WBWidget
		v-if="!configmode"
		:variable-width="true"
		:full-width="props.fullWidth"
	>
		<template #title>
			<span :style="cpNameStyle" @click="configmode = !configmode">
				<span class="fa-solid fa-charging-station">&nbsp;</span>
				{{ props.chargepoint.name }}</span
			>
		</template>

		<template #buttons>
			<span
				type="button"
				class="ms-2 ps-5 pt-1"
				:style="modePillStyle"
				@click="configmode = !configmode"
			>
				<span class="fa-solid fa-lg ps-1 fa-ellipsis-vertical" />
			</span>
		</template>

		<!-- Chargepoint info -->
		<div v-if="!configmode">
			<div class="row m-1 mt-0 p-0" @click="configmode = !configmode">
				<div class="col m-0 mb-1 p-0 d-flex justify-content-between">
					<!-- Status information -->
					<InfoItem heading="Status:">
						<span :style="{ color: statusColor }">
							<i :class="statusIcon" />
							{{ statusString }}
						</span>
					</InfoItem>

					<!-- Ladung -->
					<InfoItem heading="Geladen:">
						<FormatWattH :watt-h="chargepoint.dailyYield" />
					</InfoItem>
					<InfoItem heading="gel. Reichw.:">
						{{ chargedRangeString }}
					</InfoItem>
				</div>
			</div>
			<div
				v-if="props.chargepoint.power > 0"
				class="row m-1 p-0"
				@click="configmode = !configmode"
			>
				<div class="col m-0 p-0 d-flex justify-content-between">
					<InfoItem heading="Leistung:">
						<FormatWatt :watt="props.chargepoint.power" />
					</InfoItem>
					<InfoItem heading="Strom:">
						{{ realChargeAmpereString }}
					</InfoItem>
					<InfoItem heading="Phasen:">
						{{ props.chargepoint.phasesInUse }}
					</InfoItem>
					<InfoItem heading="Sollstrom:">
						<span class="targetCurrent">{{ chargeAmpereString }}</span>
					</InfoItem>
				</div>
			</div>
			<!-- Chargemode buttons -->
			<div class="row m-0 p-0 mt-3 mb-0">
				<div class="col d-flex justify-content-center p-0 m-0">
					<RadioBarInput
						:id="'chargemode-' + chargepoint.name"
						v-model="chargeMode"
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
				</div>
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
				<div class="row" @click="configmode = !configmode">
					<div class="col">
						<h3>
							<i class="fa-solid fa-sm fa-car me-2" />
							{{ chargepoint.vehicleName }}
							<span
								v-if="chargepoint.hasPriority"
								class="me-1 fa-solid fa-xs fa-star ps-1"
							/>
						</h3>
					</div>
				</div>
				<div class="row m-0 p-1 pt-2 mb-3">
					<!-- Car info -->

					<div class="m-0 p-0 d-flex justify-content-between">
						<InfoItem v-if="chargepoint.isSocConfigured" heading="Ladestand:">
							<BatterySymbol :soc="soc" class="me-2" />
							<i
								v-if="chargepoint.isSocConfigured && chargepoint.isSocManual"
								class="fa-solid fa-sm fas fa-edit"
								:style="{ color: 'var(--color-menu)' }"
								@click="editSoc = !editSoc"
							/>

							<i
								v-if="chargepoint.isSocConfigured && !chargepoint.isSocManual"
								type="button"
								class="fa-solid fa-sm"
								:class="
									chargepoint.waitingForSoc ? 'fa-spinner fa-spin' : 'fa-sync'
								"
								:style="{ color: 'var(--color-menu)' }"
								@click="loadSoc"
							/>
						</InfoItem>
						<InfoItem v-if="chargepoint.isSocConfigured" heading="Reichweite:">
							{{
								vehicles[props.chargepoint.connectedVehicle]
									? Math.round(
											vehicles[props.chargepoint.connectedVehicle].range,
									  )
									: 0
							}}
							km
						</InfoItem>
						<InfoItem heading="Zeitplan:">
							<span
								v-if="chargepoint.timedCharging"
								class="me-1 fa-solid fa-xs fa-clock ps-1"
							/>
							{{ props.chargepoint.timedCharging ? 'Ja' : 'Nein' }}
						</InfoItem>
					</div>

					<div
						v-if="editSoc"
						class="socEditor rounded mt-2 d-flex flex-column align-items-center"
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
					<div v-if="props.chargepoint.etActive" class="row m-1 p-0">
						<div class="col m-0 mb-1 p-0 d-flex justify-content-between">
							<InfoItem heading="max. Preis:">
								{{
									(Math.round(props.chargepoint.etMaxPrice * 10) / 10).toFixed(
										1,
									)
								}}
								ct
							</InfoItem>
							<InfoItem heading="akt. Preis:">
								<span :style="currentPriceStyle"
									>{{ currentPrice }} ct
								</span></InfoItem
							>
						</div>
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
import { updateServer } from '@/assets/js/sendMessages'
import RangeInput from '../shared/RangeInput.vue'
import { etData } from '../priceChart/model'

const props = defineProps<{
	chargepoint: ChargePoint
	fullWidth?: boolean
}>()
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
	return (
		Math.round(props.chargepoint.rangeCharged).toString() +
		' ' +
		props.chargepoint.rangeUnit
	)
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
// methods
</script>

<style scoped>
.modeIndicator {
	color: white;
}

.outlinePill {
	border: 1px solid;
	background: var(--color-bg);
	vertical-align: bottom;
	font-size: var(--font-verysmall);
}

.statusIndicator {
	border: 1px solid;
	background: 'var(--bg) ';
}

.buttonIcon {
	color: var(--color-menu);
}

.fa-star {
	color: var(--color-evu);
}

.fa-clock {
	color: var(--color-battery);
}

.fa-sliders {
	color: var(--color-menu);
}

.energylabel {
	color: var(--color-menu);
}

.vehicleName {
	color: var(--color-fg);
}

.longline {
	color: var(--color-menu);
	padding: 3;
	margin-left: 5;
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

.heading {
	color: var(--color-menu);
	font-size: var(--font-small);
}

.content {
	font-size: var(--font-normal);
	font-weight: bold;
}

.socEditor {
	border: 1px solid var(--color-menu);
}

.targetCurrent {
	color: var(--color-menu);
}
</style>
