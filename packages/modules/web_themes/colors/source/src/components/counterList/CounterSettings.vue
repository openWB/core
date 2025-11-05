<template>
	<div class="d-flex flex-column">
		<span class="settingstitle mb-3">Zähler in den Diagrammen anzeigen:</span>
		<div v-for="(element, idx) in counters.values()" :key="idx">
			<input
				:id="'check' + idx"
				v-model="element.showInGraph"
				class="form-check-input mb-3"
				type="checkbox"
				:value="element"
			/>
			<label class="form-check-label px-2" :for="'check' + idx">{{
				element.name
			}}</label>
		</div>
	</div>
</template>

<script setup lang="ts">
import { counters } from '../counterList/model'
</script>

<style scoped>
.settingstitle {
	font-weight: bold;
	font-size: var(--font-settings-title);
}
</style>
