<template>
	<WbSubwidget titlecolor="var(--color-title)" :fullwidth="true">
		<template #title>
			<span class="vehiclename">{{ props.vehicle.name }} </span>
		</template>
		<div class="d-flex justify-content-between">
			<InfoItem heading="Status:" :small="false">
				<span :style="{ color: statusColor }">{{ statusString }}</span>
			</InfoItem>
			<InfoItem heading="Ladestand:" :small="false">
				{{ Math.round(props.vehicle.soc) }} %
			</InfoItem>
			<InfoItem heading="Reichweite:" :small="false">
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
			result = 'Bereit (' + cp.name + ')'
		}
		return result
	} else {
		return 'Unterwegs'
	}
})

const statusColor = computed(() => {
	let cp = props.vehicle.chargepoint
	if (cp != undefined) {
		if (cp.isLocked) {
			return 'var(--color-evu)'
		} else if (cp.isCharging) {
			return 'var(--color-charging)'
		} else if (cp.isPluggedIn) {
			return 'var(--color-battery)'
		} else {
			return 'var(--color-axis)'
		}
	} else {
		return 'var(--color-axis)'
	}
})
</script>
<style scoped>
.idbadge {
	background-color: var(--color-menu);
	font-weight: normal;
}

.vehiclename {
	font-size: var(--font-large);
}
</style>
