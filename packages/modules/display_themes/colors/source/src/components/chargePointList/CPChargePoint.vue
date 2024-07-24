<template>
	<WBWidget v-if="!configmode" :variable-width="true">
		<template #title>
			<span :style="cpNameStyle">
				<span class="fa-solid fa-charging-station">&nbsp;</span>
				{{ props.chargepoint.name }}</span
			>
		</template>

		<template #buttons>
			<DisplayButton
				color="var(--color-cp0)"
				
				icon="fa-edit"
				@click="openSettings"
			>
				Einstellungen</DisplayButton
			>
		</template>

		<!-- Chargepoint info -->
		<div v-if="!configmode">
			<div class="grid12">
				<!-- Status information -->
				<InfoItem heading="Status:" class="grid-col-4 grid-left">
					<span :style="{ color: statusColor }">
						<i :class="statusIcon" />
						{{ statusString }}
					</span>
				</InfoItem>

				<!-- Ladung -->
				<InfoItem heading="Geladen:" class="grid-col-4">
					<FormatWattH :watt-h="chargepoint.dailyYield" />
				</InfoItem>
				<InfoItem heading="gel. Reichw.:" class="grid-col-4 grid-right">
					{{ chargedRangeString }}
				</InfoItem>

				<InfoItem
					v-if="props.chargepoint.power > 0"
					heading="Leistung:"
					class="grid-col-3 grid-left"
				>
					<FormatWatt :watt="props.chargepoint.power" />
				</InfoItem>
				<InfoItem
					v-if="props.chargepoint.power > 0"
					heading="Strom:"
					class="grid-col-3"
				>
					{{ realChargeAmpereString }}
				</InfoItem>
				<InfoItem
					v-if="props.chargepoint.power > 0"
					heading="Phasen:"
					class="grid-col-3"
				>
					{{ props.chargepoint.phasesInUse }}
				</InfoItem>
				<InfoItem
					v-if="props.chargepoint.power > 0"
					heading="Sollstrom:"
					class="grid-col-3 grid-right"
				>
					<span class="targetCurrent">{{ chargeAmpereString }}</span>
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
						<div class="d-flex justify-content-between align-items-center">
							<h3>
								<i class="fa-solid fa-sm fa-car me-2" />
								{{ chargepoint.vehicleName }}
								<span
									v-if="chargepoint.hasPriority"
									class="me-1 fa-solid fa-xs fa-star ps-1"
								/>
								<span
									v-if="chargepoint.etActive"
									class="me-0 fa-solid fa-xs fa-coins ps-0"
								/>
							</h3>
						</div>
					</div>
				</div>
				<div class="grid12">
					<!-- Car info -->
					<InfoItem
						v-if="chargepoint.isSocConfigured"
						heading="Ladestand:"
						class="grid-col-4 grid-left"
					>
						<BatterySymbol :soc="soc" class="me-2" />
					</InfoItem>
					<InfoItem
						v-if="chargepoint.isSocConfigured"
						heading="Reichweite:"
						class="grid-col-4"
					>
						{{
							vehicles[props.chargepoint.connectedVehicle]
								? Math.round(vehicles[props.chargepoint.connectedVehicle].range)
								: 0
						}}
						km
					</InfoItem>
					<InfoItem heading="Zeitplan:" class="grid-col-4 grid-right">
						<span
							v-if="chargepoint.timedCharging"
							class="me-1 fa-solid fa-xs fa-clock ps-1"
						/>
						{{ props.chargepoint.timedCharging ? 'Ja' : 'Nein' }}
					</InfoItem>

					<!-- ET Information -->
					<InfoItem
						v-if="etData.active"
						heading="Preisladen:"
						class="grid-col-4 grid-left"
					>
						<!-- <SwitchInput v-model="cp.etActive" /> -->
						{{ cp.etActive ? 'Ja' : 'Nein' }}
					</InfoItem>
					<InfoItem
						v-if="etData.active"
						heading="max. Preis:"
						class="grid-col-4"
					>
						<span type="button"
							>{{
								props.chargepoint.etActive
									? (
											Math.round(props.chargepoint.etMaxPrice * 10) / 10
										).toFixed(1) + ' ct'
									: '-'
							}}
						</span>
					</InfoItem>
					<InfoItem
						v-if="etData.active"
						heading="akt. Preis:"
						class="grid-col-4 grid-right"
					>
						<span :style="currentPriceStyle">{{ currentPrice }} ct </span>
					</InfoItem>

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
				</div>
			</div>
		</template>
	</WBWidget>
</template>

<script setup lang="ts">
import { computed, ref } from 'vue'
import { Modal } from 'bootstrap'
import { displayConfig, unlockDisplay } from '@/assets/js/model'
import { type ChargePoint, vehicles, chargePoints } from './model'
import { chargemodes } from '@/assets/js/themeConfig'
import WBWidget from '@/components/shared/WBWidget.vue'
import InfoItem from '@/components/shared/InfoItem.vue'
import CPChargeConfigPanel from './cpConfig/CPChargeConfigPanel.vue'
import BatterySymbol from '@/components/shared/BatterySymbol.vue'
import FormatWatt from '@/components/shared/FormatWatt.vue'
import FormatWattH from '../shared/FormatWattH.vue'
import RadioBarInput from '@/components/shared/RadioBarInput.vue'
import DisplayButton from '@/components/shared/DisplayButton.vue'
import { etData } from '../priceChart/model'

const props = defineProps<{
	chargepoint: ChargePoint
}>()
const cp = ref(props.chargepoint)
// computed
const chargeMode = computed({
	get() {
		return props.chargepoint.chargeMode
	},
	set(newMode) {
		if (!displayConfig.locked) {
			chargePoints[props.chargepoint.id].chargeMode = newMode
		} else {
			unlockDisplay()
		}
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
const currentPrice = computed(() => {
	const [p] = etData.etPriceList.values()
	return (Math.round(p * 10) / 10).toFixed(1)
})
function openSettings() {
	if (displayConfig.locked) {
		unlockDisplay()
	} else {
		const settingspage = new Modal('#settingspage')
		settingspage.toggle()
	}
}
</script>

<style scoped>
.fa-star {
	color: var(--color-evu);
}

.fa-clock {
	color: var(--color-battery);
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

.fa-edit {
	color: var(--color-menu);
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
.settingsbutton {
	border-radius: 30%;
}
</style>
