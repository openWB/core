<template>
	<WbWidgetFlex :variable-width="true">
		<template #title>
			<span class="fas fa-coins me-2" style="color: var(--color-battery)"
				>&nbsp;</span
			>
			<span>Strompreis</span>
		</template>
		<template #buttons>
			<WbBadge v-if="etData.active" bgcolor="var(--color-charging)">{{
				etData.etCurrentPriceString
			}}</WbBadge>
		</template>
		<div class="subtitle">{{ etData.etProvider }}</div>
		<div class="grapharea">
			<PriceChart :id="props.id" />
		</div>
	</WbWidgetFlex>
</template>

<script setup lang="ts">
import { etData } from './model'
import WbWidgetFlex from '../shared/WbWidgetFlex.vue'
import WbBadge from '../shared/WbBadge.vue'
import PriceChart from './PriceChart.vue'

const props = defineProps<{
	id: string
}>()
</script>

<style scoped>
.grapharea {
	grid-column-start: 1;
	grid-column-end: 13;
	width: 100%;
	object-fit: cover;
	max-height: 100%;
	justify-items: stretch;
}

.subtitle {
	color: var(--color-axis);
	font-size: 12px;
	grid-column: span 12;
	justify-self: start;
}
</style>
