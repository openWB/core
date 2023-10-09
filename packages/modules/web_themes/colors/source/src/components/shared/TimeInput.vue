<template>
	<input v-model="v" type="time" class="form-control" name="t" />
</template>

<script setup lang="ts">
import { computed } from 'vue'
const props = defineProps<{
	modelValue: string
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
</script>

<style scoped>
.form-control {
	background-color: var(--color-input);
	color: black;
	border: 1px solid var(--color-bg);
}
</style>
