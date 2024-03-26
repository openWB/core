<template>
	<div class="form-check form-switch">
		<input
			v-model="flag"
			class="form-check-input"
			type="checkbox"
			role="switch"
			:style="switchStyle"
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
const switchStyle = computed(() => {
	if (flag.value) {
		return { 'background-color': 'green' }
	} else {
		return { 'background-color': 'white' }
	}
})
</script>
<style scoped></style>
