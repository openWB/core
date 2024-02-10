<template>
	<WbWidgetFlex :variable-width="true" class="cptable">
		<template #title>
			<span class="fa-solid fa-charging-station">&nbsp;</span>
			Ladepunkte
		</template>
		<template #buttons>
			<div class="d-flex float-right justify-content-end align-items-center">
				<span v-if="etData.active" class="badge rounded-pill pricebadge mx-2"
					>Strompreis: {{ etData.etCurrentPriceString }}</span
				>
			</div>
		</template>
		<div
			v-for="(cp, index) in chargepointsToDisplay"
			:key="index"
			class="m-1 mt-0 p-0"
		>
			<CpsListItem2 :chargepoint="cp" />
		</div>
	</WbWidgetFlex>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import { chargePoints } from '../model'
import WbWidgetFlex from '@/components/shared/WbWidgetFlex.vue'
import CpsListItem2 from './CpsListItem2.vue'
import { etData } from '@/components/priceChart/model'
const chargepointsToDisplay = computed(() => {
	return Object.values(chargePoints)
})
</script>

<style scoped>
.tableheader {
	margin: 0;
	padding-left: 0;
	background-color: var(--color-bg);
	color: var(--color-menu);
}
.alignleft {
	text-align: left;
}
.aligncenter {
	text-align: center;
}
.alignright {
	text-align: right;
}
.table {
	border-spacing: 1rem;
	background-color: var(--color-bg);
}
.pricebadge {
	background-color: var(--color-menu);
	font-weight: normal;
}
.fa-charging-station {
	color: var(--color-charging);
}
.cptable {
	display: grid;
	grid-template-rows: [row1] auto [row2] auto;
	grid-template-columns: [left] auto [center] auto [right] auto;
	grid-gap: 1px;
}
</style>
