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
import WbBadge from '@/components/shared/WbBadge.vue'
import InfoItem from '@/components/shared/InfoItem.vue'
import FormatWattH from '@/components/shared/FormatWattH.vue'
import { formatWatt, formatTime } from '@/assets/js/helpers'

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

.buttoncell {
	background-color: var(--color-bg);
	padding: 0;
	margin: 0;
}

.left {
	text-align: left;
}

.tablecell.right {
	text-align: right;
}

.tablecolum1 {
	color: var(--color-fg);
	text-align: left;
	margin: 0;
	padding: 0;
}

.tableicon {
	color: var(--color-menu);
}

.fa-star {
	color: var(--color-evu);
}

.fa-clock {
	color: var(--color-battery);
}

.socEditor {
	border: 1px solid var(--color-menu);
	background-color: var(--color-bg);
}

.socEditRow td {
	background-color: var(--color-bg);
}

.fa-circle-check {
	color: var(--color-menu);
}

.socEditTitle {
	color: var(--color-fg);
}

.statusbadge {
	background-color: var(--color-bg);
	font-weight: bold;
	font-size: var(--font-verysmall);
}
.modebadge {
	color: var(--color-bg);
}
.cpname {
	font-size: var(--font-small);
}

.fa-edit {
	color: var(--color-menu);
}
.infolist {
	justify-content: center;
}
.devname {
	font-size: var(--font-medium);
}
</style>
