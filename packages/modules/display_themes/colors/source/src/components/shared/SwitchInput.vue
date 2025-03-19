<template>
	<div
		class="form-check form-switch d-flex align-items-center justify-content-center"
	>
		<input
			v-model="flag"
			class="form-check-input"
			type="checkbox"
			role="switch"
		/>
	</div>
</template>

<script setup lang="ts">
import { computed } from 'vue'
const props = defineProps<{
	modelValue: boolean
	onColor?: string
	offColor?: string
}>()
const emit = defineEmits(['update:modelValue'])
const flag = computed({
	get() {
		return props.modelValue
	},
	set(value: boolean) {
		emit('update:modelValue', value)
	},
})
</script>
<style scoped>
.form-switch .form-check-input {
	background-image: url("data:image/svg+xml,%3csvg xmlns='http://www.w3.org/2000/svg' viewBox='-4 -4 8 8'%3e%3ccircle r='3' fill='var(--color-fg)'/%3e%3c/svg%3e");
	background-color: var(--color-evu);
}
.form-switch .form-check-input:checked {
	background-image: url("data:image/svg+xml,%3csvg xmlns='http://www.w3.org/2000/svg' viewBox='-4 -4 8 8'%3e%3ccircle r='3' fill='white'/%3e%3c/svg%3e");
	background-color: var(--color-pv);
}
.form-switch .form-check-input {
	border: 0.1px dotted var(--color-fg);
	font-size: 20px;
	box-shadow: 2px 3px black;
}
</style>
