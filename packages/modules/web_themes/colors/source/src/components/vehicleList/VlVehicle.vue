<template>
	<WbSubwidget titlecolor="var(--color-title)" :fullwidth="true">
		<template #title>
			<span class="vehiclename">{{ props.vehicle.name }} </span>
		</template>
		<div class="d-flex justify-content-between">
			<InfoItem heading="Ladestand:" :small="true">
				{{ props.vehicle.soc }} %
			</InfoItem>
			<InfoItem heading="Reichweite:" :small="true">
				{{ props.vehicle.range }} km
			</InfoItem>
			
		</div>
	</WbSubwidget>
</template>
<script setup lang="ts">
import InfoItem from '../shared/InfoItem.vue'
import WbSubwidget from '../shared/WbSubwidget.vue'
import type { Vehicle } from '@/components/chargePointList/model.ts'
const props = defineProps<{
	vehicle: Vehicle
}>()



</script>
<style scoped>
.idbadge {
	background-color: var(--color-menu);
	font-weight: normal;
}
.vehiclename {
	font-size: var(--font-medium);
}
</style>
