<template>
	<div>
		<div class="btn-group m-0" role="group" aria-label="radiobar">
			<button
				v-for="(element, index) in options"
				:id="'radio-' + element.value"
				:key="index"
				class="btn btn-outline-secondary btn-sm radiobutton mx-0 mb-0 px-2"
				:value="element.value"
				:style="getColor(index)"
				:class="element.value == v ? 'active' : ''"
				@click="setValue"
			>
				<span :style="getColor(index)" class="scaled d-flex flex-column pt-2">
					<i v-if="element.icon" class="fa-solid" :class="element.icon" />
					{{ element.text }}
				</span>
			</button>
		</div>
	</div>
</template>

<script setup lang="ts">
import { computed } from 'vue'
const props = defineProps<{
	options: InfoItemValues[] // name, object, color, icon, active
	modelValue: number | string
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
function getColor(index: number) {
	let clr = props.options[index].color
		? props.options[index].color
		: 'var(--color-fg)'
	if (props.options[index].active) {
		return { color: 'var(--color-bg)', background: clr }
	} else {
		return { color: clr }
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
export type InfoItemValues = {
	text: string
	value: string | number
	color?: string
	icon?: string
	active: boolean
}
</script>

<style scoped>
.radiobutton {
	border: 0px solid var(--color-menu);
	opacity: 1;
	font-size: var(--font-chargebutton);
	width: 75px;
}
.btn-outline-secondary.active {
	background-color: var(--color-bg);
	border: 0px solid var(--color-fg);
	opacity: 0.8;
}
.btn-group {
	border: 0.1px solid var(--color-menu);
	box-shadow: 1px 3px black;
}
</style>
