<template>
	<!-- Fixed navbar -->

	<div class="navigation">
		<span class="graphbuttons">
			<span class="brand me-4">openWB</span>
			<DisplayButton icon="fa-chart-pie" @click="selectPowermeter"
				>Leistung</DisplayButton
			>
			<DisplayButton icon="fa-chart-line" @click="selectPowergraph"
				>Verlauf</DisplayButton
			>
			<DisplayButton icon="fa-chart-column" @click="selectEnergymeter"
				>Energie</DisplayButton
			>
		</span>

		<DisplayButton icon="fa-rectangle-list" @click="showStatus"
			>Status</DisplayButton
		>
		<span class="cpbuttons">
			<DisplayButton
				v-if="Object.values(chargePoints).length > 1"
				color="var(--color-cp0)"
				@click="cpLeft"
			>
				<span class="fas fa-arrow-left px-2" />
				<span class="fas fa-charging-station pe-2" />
			</DisplayButton>
			<DisplayButton
				:bgcolor="displayConfig.locked ? 'var(--color-evu)' : 'var(--color-pv)'"
				@click="unlockDisplay"
			>
				<span class="fas fa-lock px-4" />
			</DisplayButton>
			<DisplayButton
				v-if="Object.values(chargePoints).length > 1"
				color="var(--color-cp0)"
				@click="cpRight"
			>
				<span class="fas fa-charging-station px-2" />
				<span class="fas fa-arrow-right pe-2" />
			</DisplayButton>
			<span class="timedisplay ms-4">{{ formatCurrentTime(currentTime) }}</span>
		</span>
	</div>
</template>

<script setup lang="ts">
import { onBeforeUnmount, onMounted } from 'vue'
import { formatCurrentTime } from '@/assets/js/helpers'
import { displayConfig, currentTime, unlockDisplay } from '@/assets/js/model'
import DisplayButton from '@/components/shared/DisplayButton.vue'
import { globalConfig } from '@/assets/js/themeConfig'
import { chargePoints } from '@/components/chargePointList/model'
import { Modal } from 'bootstrap'
let interval: ReturnType<typeof setInterval>

function cpRight() {
	let cpcount = Object.values(chargePoints).length
	globalConfig.cpToShow = (globalConfig.cpToShow + 1) % cpcount
}
function cpLeft() {
	let cpcount = Object.values(chargePoints).length
	globalConfig.cpToShow =
		(((globalConfig.cpToShow - 1) % cpcount) + cpcount) % cpcount
}
function selectPowermeter() {
	globalConfig.graphToShow = 'powermeter'
}
function selectPowergraph() {
	globalConfig.graphToShow = 'powergraph'
}
function selectEnergymeter() {
	globalConfig.graphToShow = 'energymeter'
}
function showStatus() {
	if (displayConfig.locked) {
		unlockDisplay()
	} else {
		const statuspage = new Modal('#statuspage')
		statuspage.toggle()
	}
}
onMounted(() => {
	interval = setInterval(() => {
		currentTime.value = new Date()
	}, 1000)
})
onBeforeUnmount(() => {
	clearInterval(interval)
})
</script>

<style scoped>
.navigation {
	display: flex;
	justify-content: space-between;
	padding-left: 10px;
	padding-right: 10px;
	padding-top: 2px;
	padding-bottom: 2px;
	align-items: center;
	border-top: 0px solid var(--color-menu);
	border-bottom: 0px solid var(--color-menu);
}

.timedisplay {
	font-size: var(--font-medium);
	font-weight: bold;
	color: var(--color-input);
}

.navbar {
	background-color: var(--color-bg);
	color: var(--color-fg);
	font-size: var(--font-normal);
}

.graphbuttons {
	display: flex;
	justify-content: left;
	align-items: center;
	gap: 5px;
}

.cpbuttons {
	display: flex;
	justify-content: left;
	align-items: center;
	gap: 5px;
}

.dropdown-menu {
	background-color: var(--color-bg);
	color: var(--color-fg);
}

.dropdown-item {
	background-color: var(--color-bg);
	color: var(--color-fg);
	font-size: var(--font-normal);
}

.btn {
	font-size: var(--font-medium);
	background-color: var(--color-bg);
	color: var(--color-fg);
}

.navbar-brand {
	font-weight: bold;
	color: var(--color-fg);
	font-size: var(--font-normal);
}

.nav-link {
	color: var(--color-fg);
	border-color: red;
	font-size: var(--font-normal);
}

.navbar-toggler {
	color: var(--color-fg);
	border-color: var(--color-bg);
}

.navbar-time {
	font-weight: bold;
	color: var(--color-menu);
	font-size: var(--font-normal);
}

.brand {
	font-size: var(--font-medium);
	font-weight: bold;
	color: var(--color-input);
}
</style>
