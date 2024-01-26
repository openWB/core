<template>
	<WBWidget :variable-width="true">
		<template #title> Ladepunkte </template>
		<template #buttons>
			<div class="d-flex float-right justify-content-end align-items-center">
				<span v-if="etData.active" class="badge rounded-pill pricebadge mx-2"
					>Strompreis: {{ etData.etCurrentPriceString }}</span
				>
			</div>
		</template>

		<table class="table table-borderless px-0">
			<thead>
				<tr>
					<th class="tableheader alignleft">
						<i class="fa-solid fa-lg fa-charging-station ps-2" />
					</th>
					<th class="tableheader alignleft">
						<i class="fa-solid fa-lg fa-car ps-2" />
					</th>
					<th class="tableheader alignleft">
						<i class="fa-solid fa-lg fa-bolt ps-2" />
					</th>
					<th class="tableheader alignleft">
						<i class="fa-solid fa-lg fa-car-battery ps-2" />
					</th>
					<th class="tableheader alignright" />
				</tr>
			</thead>
			<tbody>
				<CPSListItem
					v-for="chargepoint in chargepointsToDisplay"
					:key="chargepoint.id"
					:chargepoint="chargepoint"
				/>
			</tbody>
		</table>
	</WBWidget>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import { chargePoints } from '../model'
import WBWidget from '@/components/shared/WBWidget.vue'
import CPSListItem from './CPSListItem.vue'
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
</style>
