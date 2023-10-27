<template>
	<WbSubwidget :titlecolor="device.color" :fullwidth="true">
		<template #title>
			{{ device.name }}
		</template>
		<template #buttons>
			<div class="d-flex float-right justify-content-end align-items-center">
				<span
					v-for="(temp, idx) in device.temp"
					:key="idx"
					class="p-0 m-0 align-items-center d-flex"
				>
					<span v-if="temp < 300" class="my-0 badge rounded-pill tempbadge mx-1"
						>{{ formatTemp(temp) }}
					</span>
				</span>
				<span
					v-if="props.device.canSwitch"
					:class="switchIcon"
					:style="switchStyle"
					class="fa statusbutton mr-2 ms-4"
					@click="statusButtonClicked"
				/>
				<span
					v-if="props.device.canSwitch"
					class="badge rounded-pill modebutton mx-2"
					@click="modeButtonClicked"
					>{{ deviceMode }}</span
				>
			</div>
		</template>
		<div class="row m-1 mt-0 p-0">
			<div class="col m-0 mb-1 p-0 d-flex justify-content-between">
				<InfoItem heading="Leistung:">
					<FormatWatt :watt="device.power" />
				</InfoItem>
				<InfoItem heading="Energie:">
					<FormatWattH :watt-h="device.energy" />
				</InfoItem>
				<InfoItem heading="Laufzeit:">
					{{ formatTime(device.runningTime) }}
				</InfoItem>
			</div>
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
import { updateServer } from '@/assets/js/sendMessages'
const props = defineProps<{
	device: ShDevice
}>()

const switchIcon = computed(() => {
	return props.device.status == 'on'
		? 'fa-toggle-on'
		: props.device.status == 'waiting'
		? 'fa-spinner fa-spin'
		: 'fa-toggle-off'
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
		shDevices[props.device.id].status = 'waiting'
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
.statusbutton {
	font-size: var(--font-large);
}

.modebutton {
	background-color: var(--color-menu);
	font-size: var(--font-verysmall);
	font-weight: normal;
}

.tempbadge {
	background-color: var(--color-battery);
	color: var(--color-bg);
	font-size: var(--font-verysmall);
	font-weight: normal;
}
</style>
