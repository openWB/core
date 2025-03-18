<template>
	<WbSubwidget titlecolor="var(--color-title)" :fullwidth="true">
		<template #title>
			<span class="vehiclename">{{ props.vehicle.name }}</span>
		</template>
		<div class="subgrid">
			<InfoItem heading="Status:" :small="true" class="grid-left grid-col-4">
				<span
					:style="{ color: statusColor }"
					class="d-flex justify-content-center align-items-center status-string"
					>{{ statusString }}</span
				>
			</InfoItem>
			<InfoItem heading="Ladestand:" :small="true" class="grid-col-4">
				<BatterySymbol :soc="soc ?? 0" color="var(--color-fg)" class="me-2" />
				<i
					v-if="vehicle.isSocManual"
					class="fa-solid fa-sm fas fa-edit"
					type="button"
					:style="{ color: 'var(--color-fg)' }"
					@click="editSoc = !editSoc"
				/>
				<i
					v-if="!vehicle.isSocManual"
					type="button"
					class="fa-solid fa-sm"
					:class="spinsymbol"
					@click="loadSoc"
				/>
			</InfoItem>
			<InfoItem
				heading="Reichweite:"
				:small="true"
				class="grid-right grid-col-4"
			>
				{{ Math.round(props.vehicle.range) }} km
			</InfoItem>
			<div
				v-if="editSoc"
				class="socEditor rounded mt-2 d-flex flex-column align-items-center grid-col-12 grid-left"
			>
				<span class="d-flex m-1 p-0 socEditTitle">Ladestand einstellen:</span>
				<span class="d-flex justify-content-stretch align-items-center">
					<span>
						<RangeInput
							id="manualSoc"
							v-model="manualSoc"
							:min="0"
							:max="100"
							:step="1"
							unit="%"
						/>
					</span>
				</span>
				<span
					type="button"
					class="fa-solid d-flex fa-lg me-2 mb-3 align-self-end fa-circle-check"
					@click="setSoc"
				/>
			</div>
		</div>
	</WbSubwidget>
</template>
<script setup lang="ts">
import { computed, ref } from 'vue'
import { chargePoints } from '@/components/chargePointList/model'
import InfoItem from '../shared/InfoItem.vue'
import WbSubwidget from '../shared/WbSubwidget.vue'
import BatterySymbol from '../shared/BatterySymbol.vue'
import RangeInput from '../shared/RangeInput.vue'
import type { Vehicle } from '@/components/chargePointList/model.ts'
import { updateServer } from '@/assets/js/sendMessages'

const props = defineProps<{
	vehicle: Vehicle
}>()
const editSoc = ref(false)
const statusString = computed(() => {
	let result = 'Unterwegs'
	let cp = props.vehicle.chargepoint
	if (cp != undefined) {
		if (cp.isCharging) {
			result = 'Lädt (' + cp.name + ')'
		} else if (cp.isPluggedIn) {
			result = 'Bereit (' + cp.name + ')'
		}
	}
	return result
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
const soc = computed(() => {
	return props.vehicle.soc
})
function loadSoc() {
	if (props.vehicle.chargepoint != undefined) {
		updateServer('socUpdate', 1, props.vehicle.id)
		chargePoints[props.vehicle.chargepoint.id].waitingForSoc = true
	}
}
function setSoc() {
	updateServer('setSoc', manualSoc.value, props.vehicle.id)
	editSoc.value = false
}
const manualSoc = computed({
	get() {
		return props.vehicle.soc
	},
	set(s: number) {
		if (props.vehicle.chargepoint != undefined) {
			chargePoints[props.vehicle.chargepoint.id].soc = s
		}
	},
})
const spinsymbol = computed(() => {
	return props.vehicle.chargepoint
		? props.vehicle.chargepoint.waitingForSoc
			? 'fa-spinner fa-spin'
			: 'fa-sync'
		: ''
})
</script>
<style scoped>
.idWbBadge {
	background-color: var(--color-menu);
	font-weight: normal;
}
.status-string {
	text-align: center;
}
.vehiclename {
	font-size: var(--font-medium);
}
.socEditor {
	border: 1px solid var(--color-menu);
	justify-self: stretch;
}
</style>
