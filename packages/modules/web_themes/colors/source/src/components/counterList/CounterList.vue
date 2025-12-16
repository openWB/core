<template>
	<WBWidgetFlex v-if="!configmode" :variable-width="true">
		<template #title>
			<span class="fas fa-bolt me-2" style="color: var(--color-evu)"
				>&nbsp;</span
			>
			<span>Zähler</span>
		</template>
		<template #buttons>
			<span
				type="button"
				class="ms-2 ps-1 pt-1"
				@click="configmode = !configmode"
			>
				<span class="fa-solid fa-lg ps-1 fa-ellipsis-vertical" />
			</span>
		</template>

		<div
			v-for="(counter, idx) in [...counters.values()]"
			:key="idx"
			class="subgrid pb-2"
		>
			<ClCounter :counter="counter" />
		</div>
	</WBWidgetFlex>
	<WBWidgetFlex v-else :variable-width="true">
		<template #title> Anzeige der Zähler </template>
		<template #buttons>
			<span class="ms-2 pt-1" @click="configmode = !configmode">
				<span class="fa-solid fa-lg ps-1 fa-circle-check" />
			</span>
		</template>
		<CounterSettings />
	</WBWidgetFlex>
</template>

<script setup lang="ts">
import { ref } from 'vue'
import WBWidgetFlex from '../shared/WbWidgetFlex.vue'
import ClCounter from './ClCounter.vue'
import CounterSettings from './CounterSettings.vue'
import { counters } from './model'

const configmode = ref(false)
</script>

<style scoped>
.statusbutton {
	font-size: var(--font-large);
}

.modebutton {
	background-color: var(--color-menu);
	font-size: var(--font-verysmall);
	font-weight: normal;
}

.tempWbBadge {
	background-color: var(--color-battery);
	color: var(--color-bg);
	font-size: var(--font-verysmall);
	font-weight: normal;
}
.fa-ellipsis-vertical {
	color: var(--color-menu);
}
.fa-circle-check {
	color: var(--color-menu);
}
.close-config-button {
	background: var(--color-menu);
	color: var(--color-bg);
	grid-column: 11 / span 2;
	font-size: var(--font-settings-button);
}
</style>
