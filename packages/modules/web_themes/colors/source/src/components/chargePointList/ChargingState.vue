<template>
	<InfoItem
		v-if="props.chargepoint.power > 0"
		heading="Leistung:"
		class="grid-col-3 grid-left mb-3"
	>
		<span style="color: var(--color-charging)">
			<FormatWatt :watt="props.chargepoint.power" /> </span
	></InfoItem>
	<InfoItem
		v-if="props.chargepoint.power > 0"
		heading="Strom:"
		class="grid-col-3"
	>
		<span style="color: var(--color-charging)">
			{{ realChargeAmpereString }}
		</span>
	</InfoItem>
	<InfoItem
		v-if="props.chargepoint.power > 0"
		heading="Phasen:"
		class="grid-col-3"
	>
		<span style="color: var(--color-charging)">
			{{ props.chargepoint.phasesInUse }}
		</span>
	</InfoItem>
	<InfoItem
		v-if="props.chargepoint.power > 0"
		heading="Sollstrom:"
		class="grid-col-3 grid-right"
	>
		<span class="targetCurrent">{{ chargeAmpereString }}</span>
	</InfoItem>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import { type ChargePoint } from './model'
import InfoItem from '@/components/shared/InfoItem.vue'
import FormatWatt from '@/components/shared/FormatWatt.vue'
const props = defineProps<{
	chargepoint: ChargePoint
	fullWidth?: boolean
}>()
const chargeAmpereString = computed(() => {
	return (
		(Math.round(props.chargepoint.current * 10) / 10).toLocaleString(
			undefined,
		) + ' A'
	)
})
const realChargeAmpereString = computed(() => {
	return (
		(Math.round(props.chargepoint.realCurrent * 10) / 10).toLocaleString(
			undefined,
		) + ' A'
	)
})
</script>
<style scoped>
.targetCurrent {
	color: var(--color-menu);
}
</style>
