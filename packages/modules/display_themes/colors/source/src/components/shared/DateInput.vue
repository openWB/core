<template>
	<span class="d-flex align-self-top justify-content-center align-items-center">
		<div class="input-group input-group-xs">
			<!-- day -->
			<button
				v-if="props.mode == 'day' || props.mode == 'today'"
				class="btn dropdown-toggle"
				type="button"
				data-bs-toggle="dropdown"
			>
				{{ day }}
			</button>
			<div class="dropdown-menu">
				<table class="table optiontable">
					<tr v-for="(line, i) in days" :key="i" class="">
						<td v-for="(myday, j) in line" :key="j">
							<span
								v-if="myday != 0"
								type="button"
								class="btn optionbutton"
								@click="day = myday"
								>{{ myday }}</span
							>
						</td>
					</tr>
				</table>
			</div>
			<!-- month -->
			<button
				v-if="props.mode != 'year' && props.mode != 'live'"
				class="btn dropdown-toggle"
				type="button"
				data-bs-toggle="dropdown"
			>
				{{ month + 1 }}
			</button>
			<div class="dropdown-menu">
				<table class="table optiontable">
					<tr v-for="(line, i) in months" :key="i" class="">
						<td v-for="(mymonth, j) in line" :key="j" class="p-0 m-0">
							<span
								type="button"
								class="btn btn-sm optionbutton"
								@click="month = mymonth"
								>{{ mymonth + 1 }}</span
							>
						</td>
					</tr>
				</table>
			</div>
			<!-- year -->
			<button
				v-if="props.mode != 'live'"
				class="btn dropdown-toggle"
				type="button"
				data-bs-toggle="dropdown"
			>
				{{ year }}
			</button>
			<div class="dropdown-menu">
				<table class="table optiontable">
					<tr v-for="(myyear, i) in years" :key="i" class="">
						<td>
							<span
								type="button"
								class="btn optionbutton"
								@click="year = myyear"
								>{{ myyear }}</span
							>
						</td>
					</tr>
				</table>
			</div>
			<button
				v-if="props.mode != 'live'"
				class="button-outline-secondary"
				type="button"
				@click="updateDate"
			>
				<span class="fa-solid fa-circle-check" />
			</button>
		</div>
	</span>
</template>

<script setup lang="ts">
import { computed, ref } from 'vue'
const props = defineProps({
	modelValue: {
		type: Date,
		required: true,
	},
	mode: {
		type: String,
		default: 'day',
	},
})
const thisYear = new Date().getFullYear()
let years = Array.from({ length: 10 }, (_, i) => thisYear - i)
const editMode = ref(true)
const emit = defineEmits(['update:modelValue'])

// const days = Array.from({ length: 31 }, (_, i) => i + 1)
const months = [
	[0, 1, 2, 3],
	[4, 5, 6, 7],
	[8, 9, 10, 11],
]
const day = ref(props.modelValue.getDate())
const month = ref(props.modelValue.getMonth())
const year = ref(props.modelValue.getFullYear())

const days = computed(() => {
	const newDate = new Date(year.value, month.value, 1)
	const firstWeekdayInMonth = newDate.getDay()
	let maxDaysPerMonth = 0
	switch (month.value) {
		case 1:
		case 3:
		case 5:
		case 7:
		case 8:
		case 10:
		case 12:
			maxDaysPerMonth = 31
			break
		case 4:
		case 6:
		case 9:
		case 11:
			maxDaysPerMonth = 30
			break
		case 2:
			if (Math.trunc(year.value / 4) * 4 == year.value) {
				maxDaysPerMonth = 29
			} else {
				maxDaysPerMonth = 28
			}
	}

	let result: number[][] = []
	let week = [0, 0, 0, 0, 0, 0, 0]
	let weekday = firstWeekdayInMonth
	for (let i = 0; i < maxDaysPerMonth; i++) {
		week[weekday] = i + 1
		if (weekday == 6) {
			result.push(week)
			week = [0, 0, 0, 0, 0, 0, 0]
			weekday = 0
		} else {
			weekday++
		}
	}
	if (weekday < 8) result.push(week)

	return result
})

function updateDate() {
	emit('update:modelValue', new Date(year.value, month.value, day.value))
	editMode.value = false
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
