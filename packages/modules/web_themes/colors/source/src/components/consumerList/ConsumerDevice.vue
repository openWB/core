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
			<span v-for="(temp, idx) in device.temp" :key="idx">
				<WbBadge v-if="temp < 300" :small="true" bgcolor="var(--color-battery)">
					<span>{{ formatTemp(temp) }} </span>
				</WbBadge>
			</span>
			<WbBadge
				v-if="device.priority > 0"
				:small="true"
				bgcolor="var(--color-menu)"
				>Prio: {{ device.priority }}
			</WbBadge>
		</template>

		<div class="subgrid pt-1">
			<transition name="status-fade">
				<div v-if="showInfo" class="statustext status-entry p-2 rounded">
					{{ device.statusText }}
				</div>
			</transition>
			<transition name="status-fade">
				<div
					v-if="showFault && device && device.faultText"
					class="faulttext status-entry p-2"
				>
					{{ device.faultText }}
				</div>
			</transition>
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
			<InfoItem heading="Leistung:" :small="true" class="grid-col-4 grid-left">
				<FormatWatt :watt="device.power"></FormatWatt>
			</InfoItem>
			<InfoItem heading="Energie:" :small="true" class="grid-col-4 grid-center">
				<FormatWattH :watt-h="device.now.energy"></FormatWattH>
			</InfoItem>
			<InfoItem heading="Laufzeit:" :small="true" class="grid-col-4 grid-right">
				{{ formatTime(device.runningTime) }}
			</InfoItem>
		</div>
	</WbSubwidget>
</template>

<script setup lang="ts">
import WbSubwidget from '@/components/shared/WbSubwidget.vue'
import type { Consumer } from './model.ts'
import { formatWatt, formatTime, formatTemp } from '@/assets/js/helpers'
import { chargemodes } from '@/assets/js/themeConfig'
import WbBadge from '@/components/shared/WbBadge.vue'
import InfoItem from '@/components/shared/InfoItem.vue'
import FormatWattH from '@/components/shared/FormatWattH.vue'
import FormatWatt from '@/components/shared/FormatWatt.vue'
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
.statustext {
	grid-column: 1 / 13;
	border: 1px solid var(--color-consumers);
	justify-self: center;
	font-size: var(--font-small);
	color: black;
	background: var(--color-menu);
}
.faulttext {
	grid-column: 1 / 13;
	border: 1px solid var(--color-consumers);
	justify-self: center;
	font-size: var(--font-small);
	color: black;
	background: var(--color-battery);
}
.status-entry {
	overflow: hidden;
	transform-origin: top center;
	will-change: opacity, transform;
}
.status-fade-enter-active,
.status-fade-leave-active {
	transition:
		opacity 0.22s cubic-bezier(0.22, 1, 0.36, 1),
		transform 0.22s cubic-bezier(0.22, 1, 0.36, 1);
}
.status-fade-enter-from {
	opacity: 0;
	transform: translateY(-6px) scaleY(0.96);
}
.status-fade-leave-to {
	opacity: 0;
	transform: translateY(-4px) scaleY(0.94);
}
.status-fade-enter-to,
.status-fade-leave-from {
	opacity: 1;
	transform: translateY(0) scaleY(1);
}
.fa-circle-info {
	color: var(--color-menu);
}
.fa-triangle-exclamation {
	color: var(--color-battery);
}
</style>
