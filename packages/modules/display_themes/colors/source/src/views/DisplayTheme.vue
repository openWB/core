<template>
	<div class="content">
		<div class="leftside">
			<CPChargePoint
				v-if="Object.values(chargePoints).length > globalConfig.cpToShow"
				:chargepoint="Object.values(chargePoints)[globalConfig.cpToShow]"
				:full-width="true"
			></CPChargePoint>
		</div>
		<div class="rightside">
			<div v-show="globalConfig.graphToShow == 'powermeter'">
				<PowerMeter></PowerMeter>
			</div>
			<div v-show="globalConfig.graphToShow == 'powergraph'">
				<PowerGraph></PowerGraph>
			</div>
			<div v-show="globalConfig.graphToShow == 'energymeter'">
				<EnergyMeter></EnergyMeter>
			</div>
		</div>
	</div>
	<ModalComponent modal-id="numberpad">
		<template #title>PIN Eingeben</template>
		<NumberPad model-value="0" @update:model-value="validateCode"></NumberPad>
	</ModalComponent>
	<ModalComponent modal-id="statuspage">
		<template #title>Systemstatus</template>
		<StatusPage></StatusPage>
	</ModalComponent>
</template>
<script setup lang="ts">
import { onMounted } from 'vue'
import { globalConfig, initConfig } from '@/assets/js/themeConfig'
import { updateDimensions } from '@/assets/js/themeConfig'
import PowerMeter from '@/components/powerMeter/PowerMeter.vue'
import PowerGraph from '@/components/powerGraph/PowerGraph.vue'
import EnergyMeter from '@/components/energyMeter/EnergyMeter.vue'
import ModalComponent from '@/components/shared/ModalComponent.vue'
import NumberPad from '@/components/shared/NumberPad.vue'
import StatusPage from '@/components/statusPage/StatusPage.vue'
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
	}
}

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
		initGraph()
	}
	//msgInit()
}
</script>
<style scoped>
.content {
	display: grid;
	grid-template-columns: 420px 380px;
	overflow: hidden;
	min-width: 0px;
}

.rightside {
	min-width: 0px;
	overflow: hidden;
}

.leftside {
	min-width: 0px;
	overflow: hidden;
}
</style>
