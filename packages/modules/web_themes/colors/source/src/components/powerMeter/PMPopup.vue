<template>
	<g>
		<rect
			x="-40"
			y="-17"
			rx="10"
			ry="10"
			width="80"
			height="40"
			corner-radius="20"
			filter="url(#f1)"
			class="popup"
			:style="{ fill: props.consumer.color }"
		/>
		<text
			dy="0"
			x="0"
			y="0"
			class="popup-textbox"
			:style="{ fill: fgColor(props.consumer.color) }"
		>
			<tspan y="0" class="popup-title">
				{{ trimLabel(props.consumer.name) }}
			</tspan>
			<tspan dy="1em" x="0" class="popup-content">
				{{ formatWatt(Math.abs(props.consumer.power)) }}
			</tspan>
		</text>
	</g>
</template>

<script lang="ts" setup>
import { formatWatt, fgColor } from '@/assets/js/helpers'
import { type PowerItem } from '@/assets/js/types'

const props = defineProps<{
	consumer: PowerItem
}>()

function trimLabel(txt: string): string {
	const MAXLENGTH = 8
	if (txt.length > MAXLENGTH) {
		return txt.substring(0, MAXLENGTH) + '.'
	}
	return txt
}
</script>
<style scoped>
.popup {
	stroke: var(--color-axis);
	stroke-width: 0.2;
	opacity: 1;
}
.popup-textbox {
	text-anchor: middle;
}
.popup-title {
	font-size: 14px;
}
.popup-content {
	font-size: 17px;
}
</style>
