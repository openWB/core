<template>
	<WbSubwidget titlecolor="var(--color-title)" :fullwidth="true">
		<template #title>
			<div class="d-flex align-items-center">
				<span class="devname" :style="{ color: device.color }"
					>{{ device.name }}
				</span>
			</div>
		</template>
		<template #buttons>
			<WbBadge v-if="device.power >= 0" bgcolor="var(--color-consumers)"
				>{{ formatWatt(device.power) }}
			</WbBadge>
		</template>

		<div class="subgrid pt-1">
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
			<InfoItem heading="Heute:" :small="true" class="grid-col-4 grid-left">
				<FormatWattH :watt-h="device.now.energy"></FormatWattH>
			</InfoItem>
			<InfoItem heading="Laufzeit:" :small="true" class="grid-col-4 grid-left">
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

const props = defineProps<{
	device: Consumer
}>()
</script>

<style scoped>
.tablerow {
	margin: 14px;
	border-top: 0.1px solid var(--color-scale);
}

.tablecell {
	color: var(--color-fg);
	background-color: var(--color-bg);
	text-align: center;
	padding-top: 2px;
	padding-left: 2px;
	padding-right: 2px;
	vertical-align: baseline;
	line-height: 1.4rem;
	font-size: var(--font-small);
}

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
</style>
