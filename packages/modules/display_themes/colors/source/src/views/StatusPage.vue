<template>
	<div class="statustable">
		<span class="header">IP-Adresse:</span
		><span>{{ globalData.ipAddress }}</span>
		<span class="header">Systemzeit:</span
		><span>{{
			new Date(globalData.systemTime * 1000).toLocaleString(undefined)
		}}</span>
		<span class="header">Version:</span><span>{{ globalData.version }}</span>
		<span class="header">Version (Details):</span
		><span>{{ globalData.versionDetails }}</span>
		<span class="header">Entwicklungszweig:</span
		><span>{{ globalData.devBranch }}</span>
	</div>

	<!-- <div v-if="!restart && !shutdown" class="controlbuttons d-flex justify-content-between p-5">
		<button class="btn controlbutton" :style="{'background-color': 'var(--color-battery)'}" @click="reload()">
			<i class="fa-solid fa-rotate-left"/>
			Display neu laden
		</button>
		<button class="btn controlbutton" :style="{'background-color': 'var(--color-evu)'}" @click="restart = true">
			<i class="fa-solid fa-power-off"/>
			openWB neu starten
		</button>
		<button class="btn controlbutton" :style="{'background-color': 'var(--color-evu)'}" @click="shutdown = true">
			<i class="fa-solid fa-power-off"/>
			openWB abschalten
		</button>
	</div> -->
	<!-- <div v-if="restart"
			class="confirmationBox rounded m-5 p-5 d-flex flex-column align-items-center "
		>
			<span class="confirmTitle">Neustart</span>
			<span class="confirmQuestion">Die openWB jetzt neu starten?</span>
			<div class="d-flex justify-content-between mt-3">
				<button class="btn cancelButton mx-3 px-3" @click="restart=false">Abbrechen</button>
				<button class="btn confirmButton mx-3 px-3" @click="restartWB()">Neustart</button>
			</div>
			
		</div> -->
		<!-- <div v-if="shutdown"
			class="confirmationBox rounded m-5 p-5 d-flex flex-column align-items-center "
		>
			<span class="confirmTitle">Abschalten</span>
			<span class="confirmQuestion">Die openWB jetzt abschalten?</span>
			<div class="d-flex justify-content-between mt-3">
				<button class="btn cancelButton mx-3 px-3" @click="shutdown=false">Abbrechen</button>
				<button class="btn confirmButton mx-3 px-3" @click="shutdownWB()">Abschalten</button>
			</div>
			
		</div> -->
</template>

<script setup lang="ts">
import { globalData } from '@/assets/js/model'
/* import { sendCommand } from '@/assets/js/sendMessages'
import { ref } from 'vue'
let restart = ref(false)
let shutdown = ref(false)

function shutdownWB() {
	sendCommand({})
}
function restartWB() {
	sendCommand({})
}
function reload() {
	location.reload()
} */
</script>

<style scoped>
.statustable {
	display: grid;
	grid-template-columns: 35% 65%;
	font-size: 16px;
	color: white;
}

.header {
	color: var(--color-fg);
}
.controlbuttons {
	font-size: var(--font-settings);
	
}
.controlbutton {
	background-color: var(--color-menu);
	color: var(--color-fg);
	font-size: var(--font-settings);
}
.confirmationBox {
	border: 3px solid var(--color-evu);
	justify-self: stretch;
	font-size: var(--font-settings);
	background-color: var(--color-fg);
	color: var(--color-evu);

}
.confirmTitle {
	font-weight: bold;
	}
.cancelButton {
	font-size: var(--font-settings);
	background-color: var(--color-battery);
}
.confirmButton {
	font-size: var(--font-settings);
	background-color: var(--color-evu);
	color: var(--color-fg);
}

</style>
