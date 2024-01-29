<template>
	<WbSubwidget titlecolor="var(--color-title)" :fullwidth="true">
		<template #title>
			<span class="vehiclename">{{ props.vehicle.name }} </span>
		</template>
		<div class="d-flex justify-content-between">
			<InfoItem heading="Status:" :small="true">
				{{ statusString }}
			</InfoItem>
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
import { computed } from 'vue'
import InfoItem from '../shared/InfoItem.vue'
import WbSubwidget from '../shared/WbSubwidget.vue'
import type { Vehicle } from '@/components/chargePointList/model.ts'

const props = defineProps<{
	vehicle: Vehicle
}>()

const statusString = computed(() => {
	let cp = props.vehicle.chargepoint
	if (cp != undefined) {
		let result = ''
		if (cp.isCharging) {
			result = 'Lädt (' + cp.name + ')'
		} else {
			result = 'Bereit'
		}
		return result
	} else {
		return '-'
	}
})
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
