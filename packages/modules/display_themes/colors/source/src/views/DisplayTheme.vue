<template>
	<div class="content">
		<div class="leftbar box">
			<CPChargePoint
				v-if="Object.values(chargePoints).length > globalConfig.cpToShow"
				:chargepoint="Object.values(chargePoints)[globalConfig.cpToShow]"
				:full-width="true"
			></CPChargePoint>
		</div>
		<div class="main box">
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
</template>
<script setup lang="ts">
//import TheWelcome from '../components/TheWelcome.vue'
import { onMounted } from 'vue'
import { globalConfig, initConfig } from '@/assets/js/themeConfig'
import {
	// globalConfig,
	updateDimensions,
	// screensize,
} from '@/assets/js/themeConfig'
import PowerMeter from '@/components/powerMeter/PowerMeter.vue'
import PowerGraph from '@/components/powerGraph/PowerGraph.vue'
import EnergyMeter from '@/components/energyMeter/EnergyMeter.vue'
import { msgInit } from '@/assets/js/processMessages'
import { initGraph } from '@/components/powerGraph/model'
import CPChargePoint from '@/components/chargePointList/CPChargePoint.vue'
import { chargePoints } from '@/components/chargePointList/model'

//import { RouterLink, RouterView } from 'vue-router'
//import HelloWorld from './components/HelloWorld.vue'
// methods
function init() {
	initConfig()
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
}
</style>
