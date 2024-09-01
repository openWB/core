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
</template>

<script setup lang="ts">
import { globalData } from '@/assets/js/model'
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
</style>
