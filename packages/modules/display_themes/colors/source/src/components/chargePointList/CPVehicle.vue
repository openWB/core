<template>
	<div class="subgrid justify-content-left">
		<div class="titleline grid-col-12 d-flex justify-content-left mb-3">
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
import { etData } from '../priceChart/model'
import { computed } from 'vue'
import { Modal, Tab } from 'bootstrap'

const props = defineProps<{
	chargepoint: ChargePoint
}>()
const cp = ref(props.chargepoint)
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
	justify-content: left;
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
</style>
