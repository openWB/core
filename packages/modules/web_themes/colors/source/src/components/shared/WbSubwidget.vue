<template>
	<div class="wb-subwidget px-3 pt-2 my-0" :class="widgetwidth">
		<div class="d-flex justify-content-between align-items-center titlerow">
			<div class="d-flex widgetname p-0 m-0" :style="titlestyle">
				<slot name="title" />
			</div>
			<div
				class="buttonrea d-flex float-right justify-content-end align-items-center"
			>
				<slot name="buttons" />
			</div>
		</div>
		<div class="contentrow grid-col-12">
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
		'font-size': 'var(--font-normal)',
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
	return props.fullwidth ? 'grid-col-12' : 'grid-col-4'
})
</script>
<style scoped>
@supports (grid-template-columns: subgrid) {
	.wb-subwidget {
		border-top: 0.5px solid var(--color-scale);
		display: grid;
		grid-template-columns: subgrid;
		grid-column: 1 / 13;
	}
}

@supports not (grid-template-columns: subgrid) {
	.wb-subwidget {
		border-top: 0.5px solid var(--color-scale);
		display: grid;
		grid-template-columns: repeat(12, auto);
		grid-column: 1 / 13;
	}
}

.titlerow {
	grid-column: 1 / 13;
}

@supports (grid-template-columns: subgrid) {
	.contentrow {
		display: grid;
		grid-template-columns: subgrid;
		grid-column: 1 / 13;
		align-items: top;
	}
}
@supports not (grid-template-columns: subgrid) {
	.contentrow {
		display: grid;
		align-items: top;
		grid-template-columns: repeat(12, auto);
	}
}

.widgetname {
	font-weight: bold;
	font-size: var(--font-large);
}
</style>
