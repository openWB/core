/* * ColorsTheme.vue * colors theme for openwb 2.0 * Copyright (c) 2022 Claus
Hagen */

<template>
	<div class="container-fluid px-2 m-0 theme-colors">
		<!-- Theme settings -->
		<div id="themesettings" class="collapse">
			<ThemeSettings @reset-arcs="resetArcs"></ThemeSettings>
		</div>
		<!-- Button Bar -->
		<ButtonBar v-if="globalConfig.showButtonBar" />

		<!-- Main Widgets -->
		<div v-if="false" class="row py-0 px-0 m-0">
			<PowerMeter />
			<PowerGraph />
			<EnergyMeter :usage-details="usageDetails" />
		</div>
		<div v-if="true" class="row py-0 px-0 m-0">
			<CarouselFix>
				<template #item1>
					<PowerMeter />
				</template>
				<template #item2>
					<PowerGraph />
				</template>
				<template #item3>
					<EnergyMeter :usage-details="usageDetails" />
				</template>
			</CarouselFix>
		</div>

		<!-- Detail configuration list -->
		<div
			v-if="!globalConfig.showQuickAccess"
			class="row py-0 m-0 d-flex justify-content-center"
		>
			<ChargePointList />
			<BatteryList />
			<SmartHomeList v-if="showSH"></SmartHomeList>
		</div>
		<!-- Tabbed area -->
		<nav
			v-if="globalConfig.showQuickAccess"
			class="nav nav-tabs nav-justified mx-1 mt-2"
			role="tablist"
		>
			<a class="nav-link active" data-bs-toggle="tab" data-bs-target="#showAll">
				<i class="fa-solid fa-lg fa-circle-info me-1" />
				<span class="d-none d-md-inline ms-2">Alles</span>
			</a>
			<a
				class="nav-link"
				data-bs-toggle="tab"
				data-bs-target="#chargepointlist"
			>
				<i class="fa-solid fa-lg fa-charging-station" />
				<span class="d-none d-md-inline ms-2">Ladepunkte</span>
			</a>
			<a
				v-if="globalData.isBatteryConfigured"
				class="nav-link"
				data-bs-toggle="tab"
				data-bs-target="#batterylist"
			>
				<i class="fa-solid fa-lg fa-car-battery" />
				<span class="d-none d-md-inline ms-2">Speicher</span>
			</a>
			<a
				v-if="showSH"
				class="nav-link"
				data-bs-toggle="tab"
				data-bs-target="#smarthomelist"
			>
				<i class="fa-solid fa-lg fa-plug" />
				<span class="d-none d-md-inline ms-2">Smart Home</span>
			</a>
			<!-- <a
				v-if="etData.isEtEnabled"
				class="nav-link"
				data-bs-toggle="tab"
				data-bs-target="#etPricing"
			>
				<i class="fa-solid fa-lg fa-money-bill-1-wave" />
				<span class="d-none d-md-inline ms-2">Strompreis</span>
			</a> -->
		</nav>
		<!-- Tab panes -->
		<div
			v-if="globalConfig.showQuickAccess"
			id="cpContent"
			class="tab-content mx-0 pt-1"
		>
			<div
				id="showAll"
				class="tab-pane active"
				role="tabpanel"
				aria-labelledby="showall-tab"
			>
				<div class="row py-0 m-0 d-flex justify-content-center">
					<ChargePointList />
					<BatteryList />
					<SmartHomeList v-if="showSH" />
				</div>
			</div>
			<div
				id="chargepointlist"
				class="tab-pane"
				role="tabpanel"
				aria-labelledby="chargepoint-tab"
			>
				<div class="row py-0 m-0 d-flex justify-content-center">
					<ChargePointList />
				</div>
			</div>
			<div
				id="batterylist"
				class="tab-pane"
				role="tabpanel"
				aria-labelledby="battery-tab"
			>
				<div class="row py-0 m-0 d-flex justify-content-center">
					<BatteryList />
				</div>
			</div>
			<div
				id="smarthomelist"
				class="tab-pane"
				role="tabpanel"
				aria-labelledby="smarthome-tab"
			>
				<div v-if="showSH" class="row py-0 m-0 d-flex justify-content-center">
					<SmartHomeList />
				</div>
			</div>
		</div>
	</div>
	<!-- Footer -->
	<div v-if="globalConfig.debug" class="row p-2 mt-5">
		<div class="col p-2">
			<hr />
			<div class="d-flex justify-content-between">
				<p class="mx-4">Screen Width: {{ screensize.x }}</p>
				<!-- <button class="btn btn-sm btn-secondary mx-4" @click="toggleSetup">
					System Setup
				</button> -->
				<button class="btn btn-sm btn-secondary mx-4" @click="toggleMqViewer">
					MQ Viewer
				</button>
			</div>
			<hr v-if="showMQ" />
			<MQTTViewer v-if="showMQ" />
		</div>
	</div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { usageSummary, globalData } from '../assets/js/model'
import { shDevices } from '@/components/smartHome/model'
import { chargePoints } from '@/components/chargePointList/model'
import { initConfig } from '@/assets/js/themeConfig'
import PowerMeter from '@/components/powerMeter/PowerMeter.vue'
import PowerGraph from '@/components/powerGraph/PowerGraph.vue'
import EnergyMeter from '@/components/energyMeter/EnergyMeter.vue'
import ChargePointList from '@/components/chargePointList/ChargePointList.vue'
import ButtonBar from '@/components/buttonBar/ButtonBar.vue'
import BatteryList from '@/components/batteryList/BatteryList.vue'
import SmartHomeList from '@/components/smartHome/SmartHomeList.vue'
import CarouselFix from '@/components/shared/CarouselFix.vue'
import { msgInit } from '@/assets/js/processMessages'
import MQTTViewer from '@/components/mqttViewer/MQTTViewer.vue'
import ThemeSettings from '@/views/ThemeSettings.vue'
import { resetArcs } from '@/assets/js/themeConfig'
import {
	globalConfig,
	updateDimensions,
	screensize,
} from '@/assets/js/themeConfig'

// state
const usageDetails = computed(() => {
	return [usageSummary.evuOut, usageSummary.devices, usageSummary.charging]
		.concat(Object.values(chargePoints).map((cp) => cp.toPowerItem()))
		.concat(
			Object.values(shDevices).filter(
				(row) => row.configured && row.showInGraph,
			),
		)
		.concat([usageSummary.batIn, usageSummary.house])
})
const showMQ = ref(false)
const showSH = computed(() => {
	return Object.values(shDevices).filter((dev) => dev.configured).length > 0
})
// methods
function init() {
	initConfig()
}
function toggleMqViewer() {
	showMQ.value = !showMQ.value
}
// lifecycle
onMounted(() => {
	init()
	window.addEventListener('resize', updateDimensions)
	window.document.addEventListener('visibilitychange', visibilityChange)
	msgInit()
})

function visibilityChange() {
	if (!document.hidden) {
		msgInit()
	}
}
</script>

<style scoped>
.nav-tabs {
	border-bottom: 0.5px solid var(--color-menu);
	background-color: var(--color-bg);
}

.nav-tabs .nav-link {
	color: var(--color-menu);
	opacity: 0.5;
}

.nav-tabs .nav-link.disabled {
	color: var(--color-axis);
	border: 0.5px solid var(--color-axis);
}

.nav-tabs .nav-link.active {
	color: var(--color-fg);
	background-color: var(--color-bg);
	opacity: 1;
	border: 0.5px solid var(--color-menu);
	border-bottom: 0px solid var(--color-menu);
	box-shadow: 0 0.5rem 1rem rgba(0, 0, 0, 0.15);
}

.fa-circle-info {
	color: var(--color-fg);
}

.fa-charging-station {
	color: var(--color-charging);
}

.fa-car-battery {
	color: var(--color-battery);
}

.fa-plug {
	color: var(--color-devices);
}

.fa-money-bill-1-wave {
	color: var(--color-pv);
}
</style>
