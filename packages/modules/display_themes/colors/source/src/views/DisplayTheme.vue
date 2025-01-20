<template>
	<div class="content">
		<div class="leftside">
			<!-- <div v-show="globalConfig.graphToShow == 'powermeter'">-->
			<PowerMeter
				v-show="globalConfig.graphToShow == 'powermeter'"
			></PowerMeter>
			<!--</div>-->
			<div v-show="globalConfig.graphToShow == 'powergraph'">
				<PowerGraph></PowerGraph>
			</div>
			<div v-show="globalConfig.graphToShow == 'energymeter'">
				<EnergyMeter></EnergyMeter>
			</div>
		</div>

		<div class="rightside">
			<CPChargePoint
				v-if="Object.values(chargePoints).length > globalConfig.cpToShow"
				:chargepoint="Object.values(chargePoints)[globalConfig.cpToShow]"
			></CPChargePoint>
		</div>
	</div>
	<ModalComponent modal-id="numberpad">
		<template #title>Code</template>
		<NumberPad model-value="" @update:model-value="validateCode"></NumberPad>
	</ModalComponent>
	<ModalComponent modal-id="statuspage">
		<template #title><span class="statustitle">Systemstatus</span></template>
		<StatusPage></StatusPage>
	</ModalComponent>
	<ModalComponent
		v-if="Object.values(chargePoints).length > globalConfig.cpToShow"
		modal-id="settingspage"
	>
		<template #title
			><span class="settingstitle"
				>Einstellungen für
				{{ Object.values(chargePoints)[globalConfig.cpToShow].vehicleName }}
				an Ladepunkt
				{{ Object.values(chargePoints)[globalConfig.cpToShow].name }}
			</span>
		</template>
		<SettingsPage
			:chargepoint="Object.values(chargePoints)[globalConfig.cpToShow]"
		></SettingsPage>
	</ModalComponent>
</template>
<script setup lang="ts">
import { onBeforeUnmount, onMounted } from 'vue'
import { globalConfig, initConfig } from '@/assets/js/themeConfig'
import { updateDimensions } from '@/assets/js/themeConfig'
import PowerMeter from '@/components/powerMeter/PowerMeter.vue'
import PowerGraph from '@/components/powerGraph/PowerGraph.vue'
import EnergyMeter from '@/components/energyMeter/EnergyMeter.vue'
import ModalComponent from '@/components/shared/ModalComponent.vue'
import NumberPad from '@/components/shared/NumberPad.vue'
import StatusPage from '@/views/StatusPage.vue'
import SettingsPage from '@/views/SettingsPage.vue'
import { msgInit } from '@/assets/js/processMessages'
import { initGraph } from '@/components/powerGraph/model'
import CPChargePoint from '@/components/chargePointList/CPChargePoint.vue'
import { chargePoints } from '@/components/chargePointList/model'
import { displayConfig, checkCode } from '@/assets/js/model'

// methods
function init() {
	initConfig()
}

function validateCode(s: string) {
	if (checkCode(s)) {
		displayConfig.locked = false
		setTimeout(() => {
			displayConfig.locked = true
		}, displayConfig.timeout * 1000)
	}
}

onMounted(() => {
	init()
	window.addEventListener('resize', updateDimensions)
	window.addEventListener('focus', haveFocus)
	//window.addEventListener('blur',lostFocus)
	msgInit()
})
onBeforeUnmount(() => {
	window.removeEventListener('focus', haveFocus)
	window.removeEventListener('resize', updateDimensions)
})
function haveFocus() {
	if (document.hasFocus()) {
		//	console.log('I have focus')
		initGraph()
	}
	//msgInit()
}
</script>
<style scoped>
.content {
	display: grid;
	grid-template-columns: 380px 420px;
	grid-template-rows: 430px;
	overflow: hidden;
	min-width: 0px;
}

.leftside {
	min-width: 0px;
	overflow: hidden;
	height: 100%;
	align-self: stretch;
}

.rightside {
	min-width: 0px;
	overflow: hidden;
	height: 100%;
	align-self: stretch;
	align-items: stretch;
}

.settingstitle {
	color: var(--color-fg);
}

.statustitle {
	color: var(--color-fg);
}
</style>
