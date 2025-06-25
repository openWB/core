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
			:style="getColors(index)"
			:class="element[1] == v ? 'active' : ''"
			@click="setValue"
		>
			<span :style="getColors(index)">
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
function getColors(index: number) {
	const fg = props.options[index][2] || 'var(--color-fg)'
	const bg = 'var(--color-bg)'
	if (props.options[index][1] == v.value) {
		return {
			color: bg,
			background: props.options[index][2] || 'var(--color-menu)',
		}
	} else {
		return { color: fg, background: bg }
	}
}
function setValue(event: Event) {
	let element = event.target as HTMLButtonElement
	while (element && !element.value && element.parentElement) {
		// we need to move up the DOM in case a sub element of the button was clicked
		element = element.parentElement as HTMLButtonElement
	}
	if (element.value) {
		v.value = element.value
	}
}
</script>

<style scoped>
.radiobutton {
	border: 0.2px solid var(--color-menu);
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
