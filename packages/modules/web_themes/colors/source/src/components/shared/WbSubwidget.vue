<template>
	<div class="wb-subwidget px-3 pt-1 my-0" :class="widgetwidth">
		<div class="d-flex justify-content-between align-items-center titlerow">
			<div class="d-flex widgetname p-0 m-0" :style="titlestyle">
				<slot name="title" />
			</div>

			<div class="buttonarea" style="text-align: right">
				<slot name="buttons" />
			</div>
		</div>
		<div class="contentrow">
			<slot />
		</div>
	</div>
</template>
<script setup lang="ts">
import { computed } from 'vue'

const props = defineProps<{
	titlecolor?: string
	fullwidth?: boolean
	small?: boolean
}>()
const titlestyle = computed(() => {
	let result = {
		'font-weight': 'bold',
		color: 'var(--color-fg)',
		'font-size': 'var(--font-extralarge)',
	}

	if (props.titlecolor) {
		result.color = props.titlecolor
	}
	if (props.small) {
		result['font-size'] = 'var(--font-verysmall)'
	}
	return result
})
const widgetwidth = computed(() => {
	return props.fullwidth ? 'col-lg-12' : 'col-lg-4'
})
</script>
<style scoped>
.wb-subwidget {
	border-top: 0.5px solid var(--color-scale);
	display: grid;
	grid-template-columns: subgrid;
	grid-column: 1 / 13;
}
.titlerow {
	grid-column: 1 / 13;
}
.contentrow {
	display: grid;
	grid-template-columns: subgrid;
	grid-column: 1 / 13;
	align-items: top;
}
.widgetname {
	font-weight: bold;
}
</style>
