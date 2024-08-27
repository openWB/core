<template>
	<WbWidgetFlex :variable-width="true">
		<template #title>
			<span class="fa-solid fa-charging-station">&nbsp;</span>
			Ladepunkte
		</template>
		<template #buttons>
			<WbBadge v-if="etData.active" bgcolor="var(--color-menu)"
				>Strompreis: {{ etData.etCurrentPriceString }}</WbBadge
			>
		</template>
		<div
			v-for="(cp, index) in chargepointsToDisplay"
			:key="index"
			class="subgrid pb-2"
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
import WbBadge from '@/components/shared/WbBadge.vue'
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

.priceWbBadge {
	background-color: var(--color-menu);
	font-weight: normal;
}

.fa-charging-station {
	color: var(--color-charging);
}
</style>
