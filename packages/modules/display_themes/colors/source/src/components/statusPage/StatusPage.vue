<template>
	<div class="statustable">
		<span >IP-Adresse:</span><span>{{ globalData.ipAddress}}</span>
		<span>Systemzeit:</span><span>{{ new Date(globalData.systemTime*1000).toLocaleString(undefined) }}</span>
		<span>Version:</span><span>{{ globalData.version }}</span>
		<span>Version (Details):</span><span>{{ globalData.versionDetails }}</span>
		<span>Entwicklungszweig:</span><span>{{ globalData.devBranch }}</span>
		
	</div>	
</template>

<script setup lang="ts">
import { globalData } from '@/assets/js/model.ts'
</script>

<style scoped>
.statustable{
	display:grid;
	grid-template-columns: 30% 70%;
	font-size: 16px;
	color:black;
	}
</style>