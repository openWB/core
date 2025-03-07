<template>
	<WBWidget>
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
		<div class="subgrid">
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
			<!-- Leistung -->
			<InfoItem
				v-if="props.chargepoint.power > 0"
				heading="Leistung:"
				class="grid-col-3 grid-left"
			>
				<FormatWatt :watt="props.chargepoint.power" />
			</InfoItem>
			<!-- Strom -->
			<InfoItem
				v-if="props.chargepoint.power > 0"
				heading="Strom:"
				class="grid-col-3"
			>
				{{ realChargeAmpereString }}
			</InfoItem>
			<!-- Phasen -->
			<InfoItem
				v-if="props.chargepoint.power > 0"
				heading="Phasen:"
				class="grid-col-3"
			>
				{{ props.chargepoint.phasesInUse }}
			</InfoItem>
			<!-- Sollstrom -->
			<InfoItem
				v-if="props.chargepoint.power > 0"
				heading="Sollstrom:"
				class="grid-col-3 grid-right"
			>
				<span class="targetCurrent">{{ chargeAmpereString }}</span>
			</InfoItem>
		</div>

		<!-- Car information-->
		<template #footer>
			<CPVehicle :chargepoint="props.chargepoint" />
		</template>
	</WBWidget>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import { Modal, Tab } from 'bootstrap'
import { displayConfig, unlockDisplay } from '@/assets/js/model'
import { type ChargePoint } from './model'
import WBWidget from '@/components/shared/WBWidget.vue'
import InfoItem from '@/components/shared/InfoItem.vue'
import FormatWatt from '@/components/shared/FormatWatt.vue'
import FormatWattH from '../shared/FormatWattH.vue'
import DisplayButton from '@/components/shared/DisplayButton.vue'
import CPVehicle from './CPVehicle.vue'

const props = defineProps<{
	chargepoint: ChargePoint
}>()
// computed
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

const cpNameStyle = computed(() => {
	return { color: props.chargepoint.color }
	// return { color: 'var(--color-fg)' }
})
function openSettings() {
	if (displayConfig.locked) {
		unlockDisplay()
	}
	const settingspage = new Modal('#settingspage')
	settingspage.toggle()
	let chargePanelName = ''
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
</script>

<style scoped>
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

.targetCurrent {
	color: var(--color-menu);
}
</style>
