<template>
	<div class="form-check form-switch">
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
