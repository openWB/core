<template>
	<div class="form-group">
		<input id="name" v-model="v" type="text" class="form-control" />
	</div>
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
.form-select {
	background-color: var(--color-input);
	color: black;
	border: 1px solid var(--color-bg);
	font-size: var(--font-settings);
}
</style>
