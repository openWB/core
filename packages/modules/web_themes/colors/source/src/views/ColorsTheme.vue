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
			<EnergyMeter />
			<ChargePointList id="0" :compact="globalConfig.shortCpList == 'always'" />
			<GlobalPriceChart id="Hidden" />
			<VehicleList />
			<CounterList />
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
					<EnergyMeter />
				</template>
			</CarouselFix>
		</div>

		<!-- Detail configuration list -->
		<div
			v-if="!globalConfig.showQuickAccess"
			class="row py-0 m-0 d-flex justify-content-center"
		>
			<ChargePointList id="1" :compact="globalConfig.shortCpList == 'always'" />
			<GlobalPriceChart
				v-if="globalConfig.showPrices"
				id="NoTabs"
			></GlobalPriceChart>
			<VehicleList v-if="globalConfig.showVehicles"></VehicleList>
			<BatteryList />
			<SmartHomeList v-if="showSH"></SmartHomeList>
			<CounterList v-if="globalConfig.showCounters"></CounterList>
			<InverterList v-if="globalConfig.showInverters"></InverterList>
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
				v-if="globalConfig.showPrices"
				class="nav-link"
				data-bs-toggle="tab"
				data-bs-target="#pricecharttabbed"
			>
				<i class="fa-solid fa-lg fa-coins" />
				<span class="d-none d-md-inline ms-2">Strompreis</span>
			</a>
			<a
				v-if="globalConfig.showVehicles"
				class="nav-link"
				data-bs-toggle="tab"
				data-bs-target="#vehiclelist"
			>
				<i class="fa-solid fa-lg fa-car" />
				<span class="d-none d-md-inline ms-2">Fahrzeuge</span>
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
			<a
				v-if="globalConfig.showCounters"
				class="nav-link"
				data-bs-toggle="tab"
				data-bs-target="#counterlist"
			>
				<i class="fa-solid fa-lg fa-bolt" />
				<span class="d-none d-md-inline ms-2">Zähler</span>
			</a>
			<a
				v-if="globalConfig.showInverters"
				class="nav-link"
				data-bs-toggle="tab"
				data-bs-target="#inverterlist"
			>
				<i class="fa-solid fa-lg fa-solar-panel" />
				<span class="d-none d-md-inline ms-2">Wechselrichter</span>
			</a>
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
					<ChargePointList id="2" :compact="globalConfig.shortCpList != 'no'" />
					<GlobalPriceChart v-if="globalConfig.showPrices" id="Overview" />
					<VehicleList v-if="globalConfig.showVehicles" />
					<BatteryList />
					<SmartHomeList v-if="showSH" />
					<CounterList v-if="globalConfig.showCounters" />
					<InverterList v-if="globalConfig.showInverters" />
				</div>
			</div>
			<div
				id="chargepointlist"
				class="tab-pane"
				role="tabpanel"
				aria-labelledby="chargepoint-tab"
			>
				<div class="row py-0 m-0 d-flex justify-content-center">
					<ChargePointList
						id="3"
						:compact="globalConfig.shortCpList == 'always'"
					/>
				</div>
			</div>
			<div
				id="vehiclelist"
				class="tab-pane"
				role="tabpanel"
				aria-labelledby="vehicle-tab"
			>
				<div
					v-if="globalConfig.showVehicles"
					class="row py-0 m-0 d-flex justify-content-center"
				>
					<VehicleList />
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
			<div
				id="counterlist"
				class="tab-pane"
				role="tabpanel"
				aria-labelledby="counter-tab"
			>
				<div
					v-if="globalConfig.showCounters"
					class="row py-0 m-0 d-flex justify-content-center"
				>
					<CounterList />
				</div>
			</div>
			<div
				id="inverterlist"
				class="tab-pane"
				role="tabpanel"
				aria-labelledby="inverter-tab"
			>
				<div
					v-if="globalConfig.showInverters"
					class="row py-0 m-0 d-flex justify-content-center"
				>
					<InverterList />
				</div>
			</div>
			<div
				id="pricecharttabbed"
				class="tab-pane"
				role="tabpanel"
				aria-labelledby="price-tab"
			>
				<div
					v-if="globalConfig.showPrices"
					class="row py-0 m-0 d-flex justify-content-center"
				>
					<GlobalPriceChart id="Tabbed" />
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
import { globalData } from '../assets/js/model'
import { shDevices } from '@/components/smartHome/model'
import { initConfig } from '@/assets/js/themeConfig'
import PowerMeter from '@/components/powerMeter/PowerMeter.vue'
import PowerGraph from '@/components/powerGraph/PowerGraph.vue'
import EnergyMeter from '@/components/energyMeter/EnergyMeter.vue'
import ChargePointList from '@/components/chargePointList/ChargePointList.vue'
import ButtonBar from '@/components/buttonBar/ButtonBar.vue'
import BatteryList from '@/components/batteryList/BatteryList.vue'
import SmartHomeList from '@/components/smartHome/SmartHomeList.vue'
import CounterList from '@/components/counterList/CounterList.vue'
import VehicleList from '@/components/vehicleList/VehicleList.vue'
import GlobalPriceChart from '@/components/priceChart/GlobalPriceChart.vue'
import InverterList from '@/components/inverterList/InverterList.vue'
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
import { initGraph } from '@/components/powerGraph/model'

// state
const showMQ = ref(false)
const showSH = computed(() => {
	return [...shDevices.values()].filter((dev) => dev.configured).length > 0
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
	window.addEventListener('focus', haveFocus)
	//window.addEventListener('blur',lostFocus)
	msgInit()
})

function haveFocus() {
	if (document.hasFocus()) {
		//	console.log('I have focus')
		initGraph(true) // reload only
	}
	//msgInit()
}
/* function lostFocus() {
	if (!document.hasFocus()) {
		console.log('I lost focus')
	}
//	msgStop()
} */
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

.fa-bolt {
	color: var(--color-evu);
}

.fa-car {
	color: var(--color-charging);
}

.fa-coins {
	color: var(--color-battery);
}
.fa-solar-panel {
	color: var(--color-pv);
}
</style>
