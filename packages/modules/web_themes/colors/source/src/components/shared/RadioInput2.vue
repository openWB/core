<template>
	<div
		class="buttongrid"
		:style="{
			'grid-template-columns': 'repeat(' + (props.columns || 3) + ', 1fr)',
		}"
	>
		<button
			v-for="(element, index) in props.options"
			:id="'radio-' + element[1]"
			:key="index"
			class="btn btn-outline-secondary radiobutton me-0 mb-0 px-2"
			:value="element[1]"
			:style="buttonStyle(index)"
			:class="element[1] == v ? 'active' : ''"
			@click="setValue"
		>
			<span>
				<i v-if="element[3]" class="fa-solid" :class="element[3]" />
				{{ element[0] }}
			</span>
		</button>
	</div>
</template>

<script setup lang="ts">
import { computed } from 'vue'
const props = defineProps<{
	options: [number | string, number | string, string?, string?][]
	modelValue: number | string
	columns?: number
}>()
const emit = defineEmits(['update:modelValue'])
const v = computed({
	get() {
		return props.modelValue
	},
	set(value: number | string) {
		emit('update:modelValue', value)
	},
})
function buttonStyle(index: number) {
	const fg = props.options[index][2] || 'var(--color-fg)'
	const bg = 'var(--color-bg)'
	let color = fg
	let background = bg
	let borderRadius = ['0', '0', '0', '0'] // top-left, top-right, bottom-right, bottom-left
	let borderWidth = ['0', '0', '0', '0'] // top, right, bottom, left
	if (props.options[index][1] == v.value) {
		color = bg
		background = props.options[index][2] || 'var(--color-menu)'
	}

	const optionCount = props.options.length
	const col = index % 3
	const row = Math.floor(index / 3)
	const maxRow = Math.floor((optionCount - 1) / 3)
	if (col == 0) {
		if (row == 0) {
			borderRadius[0] = '0.45rem' // top-left
		}
		if (row == maxRow) {
			borderRadius[3] = '0.45rem' // bottom-left
		}
		borderWidth[1] = '0.1px' // right
	}
	if (col == 1) {
		borderWidth[1] = '0.1px' // right
		borderWidth[3] = '0.1px' // left
	}
	if (col == 2) {
		if (row == 0) {
			borderRadius[1] = '0.45rem' // top-right
		}
		if (row == maxRow) {
			borderRadius[2] = '0.45rem' // bottom-right
		}
		borderWidth[3] = '0.1px' // left
	}
	if (row != 0) {
		borderWidth[0] = '0.1px' // top
	}
	if (row != maxRow) {
		borderWidth[2] = '0.1px' // bottom
	}

	return {
		color: color,
		background: background,
		'border-radius': `${borderRadius[0]} ${borderRadius[1]} ${borderRadius[2]} ${borderRadius[3]}`,
		'border-width': `${borderWidth[0]} ${borderWidth[1]} ${borderWidth[2]} ${borderWidth[3]}`,
	}
}
function setValue(event: Event) {
	let element = event.target as HTMLButtonElement
	while (element && !element.value && element.parentElement) {
		// we need to move up the DOM in case a sub element of the button was clicked
		element = element.parentElement as HTMLButtonElement
	}
	if (element.value) {
		if (typeof props.options[0][1] === 'number') {
			v.value = Number(element.value)
		} else {
			v.value = element.value
		}
	}
}
</script>

<style scoped>
.radiobutton {
	border: 0.1px solid var(--color-menu);
	opacity: 1;
	font-size: var(--font-settings-button);
	border-radius: 0;
}
.btn-outline-secondary.active {
	background-color: var(--color-fg);
	border: 1px solid var(--color-menu);
	box-shadow: 0 0.5rem 1rem rgba(0, 0, 0, 0.15);
	opacity: 1;
}
.buttongrid {
	display: grid;
	border: 1px solid var(--color-menu);
	border-radius: 0.5rem;
	justify-items: stretch;
	justify-self: stretch;
	width: 100%;
}
</style>
