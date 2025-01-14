<template>
	<WbSubwidget :titlecolor="device.color" :fullwidth="true">
		<template #title>
			<span class="devicename">
				{{ device.name }}
			</span>
		</template>
		<template #buttons>
			<span v-for="(temp, idx) in device.temp" :key="idx">
				<WbBadge v-if="temp < 300" bgcolor="var(--color-battery)">
					<span>{{ formatTemp(temp) }} </span>
				</WbBadge>
			</span>
			<span
				v-if="props.device.canSwitch"
				:class="switchIcon"
				:style="switchStyle"
				class="fa-solid statusbutton mr-2 ms-2"
				@click="statusButtonClicked"
			/>
			<WbBadge
				v-if="props.device.canSwitch"
				type="button"
				@click="modeButtonClicked"
			>
				{{ deviceMode }}
			</WbBadge>
		</template>
		<div class="subgrid">
			<InfoItem heading="Leistung:" :small="true" class="grid-col-4 grid-left">
				<FormatWatt :watt="device.power" />
			</InfoItem>
			<InfoItem heading="Energie:" :small="true" class="grid-col-4">
				<FormatWattH :watt-h="device.energy" />
			</InfoItem>
			<InfoItem heading="Laufzeit:" :small="true" class="grid-col-4 grid-right">
				{{ formatTime(device.runningTime) }}
			</InfoItem>
		</div>
	</WbSubwidget>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import { type ShDevice, shDevices } from './model'
import { formatTime, formatTemp } from '@/assets/js/helpers'
import WbSubwidget from '../shared/WbSubwidget.vue'
import InfoItem from '../shared/InfoItem.vue'
import FormatWatt from '../shared/FormatWatt.vue'
import FormatWattH from '../shared/FormatWattH.vue'
import WbBadge from '../shared/WbBadge.vue'
import { updateServer } from '@/assets/js/sendMessages'
const props = defineProps<{
	device: ShDevice
}>()

const switchIcon = computed(() => {
	return props.device.status == 'on'
		? 'fa-toggle-on fa-xl'
		: props.device.status == 'waiting'
			? 'fa-spinner fa-spin'
			: 'fa-toggle-off fa-xl'
})
const switchStyle = computed(() => {
	let swColor = 'var(--color-switchRed)'

	switch (props.device.status) {
		case 'on':
			swColor = 'var(--color-switchGreen)'
			break
		case 'detection':
			swColor = 'var(--color-switchBlue)'
			break
		case 'timeout':
			swColor = 'var(--color-switchWhite)'
			break
		case 'waiting':
			swColor = 'var(--color-menu)'
			break
		default:
			swColor = 'var(--color-switchRed)'
	}

	return { color: swColor }
})
function statusButtonClicked() {
	if (!props.device.isAutomatic) {
		if (props.device.status == 'on') {
			updateServer('shSwitchOn', 0, props.device.id)
		} else {
			updateServer('shSwitchOn', 1, props.device.id)
		}
		shDevices.get(props.device.id)!.status = 'waiting'
	}
}
function modeButtonClicked() {
	if (props.device.isAutomatic) {
		updateServer('shSetManual', 1, props.device.id)
	} else {
		updateServer('shSetManual', 0, props.device.id)
	}
}
const deviceMode = computed(() => {
	if (props.device.isAutomatic) {
		return 'Auto'
	} else {
		return 'Man'
	}
})
</script>

<style scoped>
.devicename {
	font-size: var(--font-medium);
}
.statusbutton {
	font-size: var(--font-extralarge);
}
</style>
