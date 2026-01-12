<template>
	<span class="p-1 m-1">
		<div class="input-group">
			<input
				:id="inputId"
				class="form-control"
				type="date"
				pattern="\d{2}.\d{2}.\d{4}"
				placeholder="DD.MM.YYYY"
			/>
		</div>
	</span>
</template>

<script setup lang="ts">
import { onMounted } from 'vue'
const props = defineProps({
	inputId: {
		type: String,
		required: true,
	},
	modelValue: {
		type: Date,
		required: true,
	},
})

var dateInput = document.getElementById('inputDate') as HTMLInputElement
const emit = defineEmits(['update:modelValue'])

function updateDate(d: Date) {
	emit('update:modelValue', d)
}

onMounted(() => {
	dateInput = document.getElementById(props.inputId) as HTMLInputElement
	dateInput.value = props.modelValue.toISOString().substring(0, 10)
	dateInput.addEventListener('change', handleChangeEvent)
})

function handleChangeEvent(event: Event) {
	const target = event.target as HTMLInputElement
	const dateParts = target.value.split('-')
	const year = parseInt(dateParts[0])
	const month = parseInt(dateParts[1]) - 1
	const day = parseInt(dateParts[2])
	updateDate(new Date(year, month, day))
}
</script>

<style scoped>
.form-select {
	background-color: var(--color-input);
	border: 1;
	border-color: var(--color-bg);
	color: var(--color-bg);
	text-align: start;
	font-size: var(--font-small);
}

.commitbutton {
	background-color: var(--color-bg);
	color: var(--color-input);
}

option {
	color: green;
}

.form-select {
	font-size: var(--font-verysmall);

	background-color: var(--color-menu);
	color: var(--color-fg);
}
.optiontable {
	background-color: var(--color-menu);
}
.optionbutton {
	font-size: var(--font-small);
	color: white;
	background-color: var(--color-menu);
	font-size: var(--font-verysmall);
	text-align: center;
}
.dropdown-menu {
	background-color: var(--color-menu);
}
.dropdown-toggle {
	background-color: var(--color-menu);
	color: white;
	border: 1px solid var(--color-bg);
	font-size: var(--font-verysmall);
}
</style>
