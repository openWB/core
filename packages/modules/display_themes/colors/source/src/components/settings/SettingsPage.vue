<template>
	<div class="settingslist">
		<ConfigItem
			v-if="globalData.isBatteryConfigured"
			title="PV-Priorität (global)"
			icon="fa-car-battery"
			infotext="Priority during PV production"
			:fullwidth="true"
		>
			<RadioInput
				v-model="globalData.pvBatteryPriority"
				:options="evPriorityModes"
			>
			</RadioInput>
		</ConfigItem>
		<hr class="grid-col-12" />
		<ConfigItem
			title="Strompreisbasiert laden"
			icon="fa-coins"
			infotext="Settings"
		>
			<SwitchInput v-model="etActive"></SwitchInput>
		</ConfigItem>
		<ConfigItem title="Zeitplan aktivieren" icon="fa-coins" infotext="Settings">
			<SwitchInput v-model="timedCharging"></SwitchInput>
		</ConfigItem>
	</div>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import { globalData } from '@/assets/js/model'
import { chargePoints, type ChargePoint } from '@/components/chargePointList/model'
import ConfigItem from '@/components/shared/ConfigItem.vue'
import RadioInput from '@/components/shared/RadioInput.vue'
import SwitchInput from '@/components/shared/SwitchInput.vue'
import { evPriorityModes } from '@/assets/js/types'
const props = defineProps<{
	chargepoint: ChargePoint
}>()
const etActive = computed({
	get: () => props.chargepoint.etActive,
	set: (value: boolean) => {
		chargePoints[props.chargepoint.id].etActive = value
	},
})
const timedCharging = computed({
	get: () => props.chargepoint.timedCharging,
	set: (value: boolean) => {
		chargePoints[props.chargepoint.id].timedCharging = value
	},
})
</script>

<style scoped>
.settingslist {
	display: grid;
	grid-template-columns: repeat(12, 1fr);
	font-size: 16px;
	color: black;
}
</style>
