<template>
	<WbSubwidget titlecolor="var(--color-title)" :fullwidth="true">
		<template #title>
			<div class="d-flex align-items-center">
				<span class="devname" :style="{ color: device.color }"
					>{{ device.name }}
				</span>
				<span>
					<i
						v-if="device.faultState === 0"
						@click="showInfo = !showInfo"
						class="fa-solid fa-sm fa-circle-info ms-2"
					/>
					<i
						v-if="device.faultState != 0"
						@click="showFault = !showFault"
						class="fa-solid fa-sm fa-triangle-exclamation ms-2"
					/>
				</span>
			</div>
		</template>
		<template #buttons>
			<WbBadge v-if="device.priority > 0" bgcolor="var(--color-menu)"
				>Prio: {{ device.priority }}
			</WbBadge>
			<WbBadge v-if="device.power >= 0" bgcolor="var(--color-consumers)"
				>{{ formatWatt(device.power) }}
			</WbBadge>
		</template>

		<div class="subgrid pt-1">
			<div v-if="showInfo" class="devicestatus p-2 rounded">
				{{ device.statusText }}
			</div>
			<div v-if="showFault" class="devicestatus p-2">
				{{ device.faultText }}
			</div>
			<RadioBarInput
				:id="'chargemode-' + device.name"
				v-model="device.chargeMode"
				class="chargemodes mt-3 mb-3"
				:options="
					Object.entries(chargemodes).map((v) => {
						return {
							text: v[1].name,
							value: v[0],
							color: v[1].color,
							icon: v[1].icon,
							active: v[1].mode == device.chargeMode,
						}
					})
				"
			/>
			<InfoItem heading="Heute:" :small="true" class="grid-col-6 grid-left">
				<FormatWattH :watt-h="device.now.energy"></FormatWattH>
			</InfoItem>
			<InfoItem heading="Laufzeit:" :small="true" class="grid-col-6 grid-left">
				{{ formatTime(device.runningTime) }}
			</InfoItem>
		</div>
	</WbSubwidget>
</template>

<script setup lang="ts">
import WbSubwidget from '@/components/shared/WbSubwidget.vue'
import type { Consumer } from './model.ts'
import { formatWatt, formatTime } from '@/assets/js/helpers'
import { type ChargeModeInfo } from '@/assets/js/types'
import { chargemodes } from '@/assets/js/themeConfig'
import WbBadge from '@/components/shared/WbBadge.vue'
import InfoItem from '@/components/shared/InfoItem.vue'
import FormatWattH from '@/components/shared/FormatWattH.vue'
import RadioBarInput from '../shared/RadioBarInput.vue'
import { ref } from 'vue'

const props = defineProps<{
	device: Consumer
}>()

const showInfo = ref(false)
const showFault = ref(false)
</script>

<style scoped>
.left {
	text-align: left;
}

.tablecell.right {
	text-align: right;
}

.devname {
	font-size: var(--font-medium);
}
.chargemodes {
	grid-column: 1 / 13;
	justify-self: center;
}
.devicestatus {
	grid-column: 1 / 13;
	border: 1px solid var(--color-consumers);
	justify-self: center;
	font-size: var(--font-small);
	color: black;
	background: var(--color-menu);
}
.fa-circle-info {
	color: var(--color-charging);
}
.fa-triangle-exclamation {
	color: var(--color-battery);
}
</style>
