<template>
	<div class="vehicleinfo justify-content-left">
		<div class="titleline mb-3">
			<DisplayButton @click="openSettings('#chSettings')">
				<div
					class="carname d-flex justify-content-left align-items-center px-2"
				>
					<i class="fa-solid fa-sm fa-car me-3" />
					{{ chargepoint.vehicleName }}
					<span
						v-if="chargepoint.hasPriority"
						class="ms-2 me-0 fa-solid fa-xs fa-star ps-1"
					/>
					<span
						v-if="chargepoint.etActive"
						class="ms-2 me-0 fa-solid fa-xs fa-coins ps-0"
					/>
				</div>
			</DisplayButton>
		</div>
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
				class="fa-solid d-flex fa-lg m-3 me-1 mb-4 align-self-end fa-circle-check"
				@click="setSoc"
			/>
		</div>
		<!-- Car info -->
		<div class="infoline">
			<InfoItem
				v-if="chargepoint.isSocConfigured"
				heading="Ladestand:"
				class="grid-col-4 grid-left"
			>
				<BatterySymbol :soc="soc" class="me-2" />
				<DisplayButton
					v-if="chargepoint.isSocManual"
					@click="editSoc = !editSoc"
				>
					<i
						class="fa-solid fa-sm fas fa-edit py-0 px-3 mt-3"
						:style="{ color: 'var(--color-fg)' }"
					/>
				</DisplayButton>
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
		</div>
		<div class="infoline">
			<!-- ET Information -->
			<InfoItem
				v-if="etData.active"
				heading="Preisladen:"
				class="grid-col-4 grid-left"
			>
				<SwitchInput v-model="cp.etActive" />
				<!--{{ cp.etActive ? 'Ja' : 'Nein' }}-->
			</InfoItem>

			<InfoItem v-if="etData.active" heading="max. Preis:" class="grid-col-4">
				<DisplayButton v-if="cp.etActive" @click="openSettings('#prSettings')">
					<span class="maxprice"
						>{{
							props.chargepoint.etActive
								? (Math.round(props.chargepoint.etMaxPrice * 10) / 10).toFixed(
										1,
									) + ' ct'
								: '-'
						}}
					</span>
				</DisplayButton>
				<span v-else>-</span>
			</InfoItem>

			<InfoItem
				v-if="etData.active"
				heading="akt. Preis:"
				class="grid-col-4 grid-right"
			>
				<span :style="currentPriceStyle">{{ currentPrice }} ct </span>
			</InfoItem>
		</div>
		<!-- Chargemode buttons -->
		<RadioBarInput
			:id="'chargemode-' + chargepoint.name"
			v-model="chargeMode"
			class="chargemodes mx-3 mt-4 mb-0"
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
</template>
<script setup lang="ts">
import { displayConfig, unlockDisplay } from '@/assets/js/model'
import { type ChargePoint, chargePoints, vehicles } from './model'
import { chargemodes } from '@/assets/js/themeConfig'
import { ref } from 'vue'

import InfoItem from '@/components/shared/InfoItem.vue'
import BatterySymbol from '@/components/shared/BatterySymbol.vue'
import RadioBarInput from '@/components/shared/RadioBarInput.vue'
import DisplayButton from '@/components/shared/DisplayButton.vue'
import SwitchInput from '../shared/SwitchInput.vue'
import RangeInput from '../shared/RangeInput.vue'
import { etData } from '../priceChart/model'
import { computed } from 'vue'
import { Modal, Tab } from 'bootstrap'
import { updateServer } from '@/assets/js/sendMessages'

const props = defineProps<{
	chargepoint: ChargePoint
}>()
const cp = ref(props.chargepoint)
const editSoc = ref(false)

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
const soc = computed(() => {
	return props.chargepoint.soc
})
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
const currentPrice = computed(() => {
	const [p] = etData.etPriceList.values()
	return (Math.round(p * 10) / 10).toFixed(1)
})
function openSettings(target: string = '') {
	if (displayConfig.locked) {
		unlockDisplay()
	}
	const settingspage = new Modal('#settingspage')
	settingspage.toggle()
	let chargePanelName = target
	if (target == '') {
		switch (props.chargepoint.chargeMode) {
			case 'instant_charging':
				chargePanelName = '#inSettings'
				break
			case 'pv_charging':
				chargePanelName = '#phvSettings'
				break
			case 'scheduled_charging':
				chargePanelName = '#scSettings'
				break
			default:
				chargePanelName = '#chSettings'
		}
	}

	const tabToActivate = document.querySelector(
		chargePanelName + props.chargepoint.id,
	)
	if (tabToActivate) {
		var tab = new Tab(tabToActivate)
		tab.show()
	} else {
		console.error('no element found')
	}
}

const currentPriceStyle = computed(() => {
	return props.chargepoint.etMaxPrice >= +currentPrice.value
		? { color: 'var(--color-charging)' }
		: { color: 'var(--color-menu)' }
})
</script>
<style scoped>
.titleline {
	display: flex;
	justify-content: left;
}
.infoline {
	display: flex;
	justify-content: space-between;
	flex-direction: row;
}
.chargemodes {
	grid-column: 1 / 13;
	justify-self: center;
}

.carname {
	color: var(--color-fg);
	font-size: var(--font-medium);
}

.maxprice {
	font-size: var(--font-medium);
	color: var(--color-fg);
}

.fa-star {
	color: var(--color-evu);
}
.fa-circle-check {
	font-size: 20pt;
}
.fa-edit {
	font-size: 8pt;
}
.socEditor {
	border: 1px solid var(--color-menu);
	justify-self: stretch;
}
.vehicleinfo {
	display: flex;
	flex-direction: column;
}
</style>
