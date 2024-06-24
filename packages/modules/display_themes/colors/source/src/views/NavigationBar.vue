<template>
	<!-- Fixed navbar -->

	<div class="navigation">
		<span class="timedisplay">{{ formatCurrentTime(currentTime) }}</span>
		<DisplayButton @click="cpLeft">
			<span class="fas fa-arrow-left px-2" />
			<span class="fas fa-charging-station pe-2" />
		</DisplayButton>
		<DisplayButton @click="cpRight">
			<span class="fas fa-charging-station px-2" />
			<span class="fas fa-arrow-right pe-2" />
		</DisplayButton>
		<DisplayButton :color= "(displayConfig.locked) ? 'var(--color-evu)' : 'var(--color-pv)'" @click="unlockDisplay">
			<span class="fas fa-lock px-4" />
		</DisplayButton>
		<DisplayButton data-bs-toggle="modal" data-bs-target="#statuspage">Status</DisplayButton>
		<DisplayButton icon="fa-chart-pie" @click="selectPowermeter">Leistung</DisplayButton>
		<DisplayButton icon="fa-chart-line" @click="selectPowergraph">Verlauf</DisplayButton>
		<DisplayButton icon="fa-chart-column" @click="selectEnergymeter">Energie</DisplayButton>
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
	console.log('Charge Point clicked')
	let cpcount = Object.values(chargePoints).length
	globalConfig.cpToShow = (globalConfig.cpToShow + 1) % cpcount
}
function cpLeft() {
	console.log('Charge Point clicked')
	let cpcount = Object.values(chargePoints).length
	globalConfig.cpToShow =
		(((globalConfig.cpToShow - 1) % cpcount) + cpcount) % cpcount
	console.log(globalConfig.cpToShow)
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
	border-top: 0.1px solid var(--color-menu);
	border-bottom: 1px solid var(--color-menu);
}

.mybutton {
	border: 10px;
	padding: 8px;
	align-self: top;
	background-color: var(--color-menu);
	border-radius: 8px;
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
</style>
