<template>
	<div
		class="d-flex flex-column justify-content-center pgselector rounded"
		:style="selectorstyle"
	>
		<RadioBarInput
			v-if="editmode == 2"
			id="pgm2"
			v-model="gmode"
			class="m-2"
			:options="
				graphmodes.map((v, i) => {
					return {
						text: modenames[i],
						value: v,
						color: 'var(--color-menu)',
						active: v == graphData.graphMode,
					}
				})
			"
		/>
		<!-- Row 1 -->
		<!-- Up-Button -->
		<span
			v-if="editmode == 1"
			type="button"
			class="arrowButton d-flex align-self-center mb-3 mt-3"
			:class="{ disabled: !props.showLeftButton }"
			@click="$emit('shiftUp')"
		>
			<i class="fa-solid fa-xl fa-chevron-circle-up" />
		</span>
		<!-- Row 2 -->
		<div class="d-flex align-items-center" :class="row2layout">
			<!-- Left Button -->
			<span
				v-if="editmode == 1"
				type="button"
				class="p-1"
				:class="{ disabled: !props.showLeftButton }"
				@click="$emit('shiftLeft')"
			>
				<span class="fa-solid fa-xl fa-chevron-circle-left arrowButton" />
			</span>
			<!-- badge -->
			<span
				v-if="editmode < 2"
				type="button"
				class="btn-outline-secondary p-2 px-3 badge rounded-pill datebadge"
				@click="toggleEdit"
			>
				{{ displayDate }}
			</span>
			<DateInput
				v-if="editmode == 2"
				:model-value="graphdate"
				:mode="graphData.graphMode"
				@update:model-value="setDate"
			/>

			<!-- Right Button -->
			<span
				v-if="editmode == 1"
				id="graphRightButton"
				type="button"
				class="arrowButton fa-solid fa-xl fa-chevron-circle-right p-1"
				:class="{ disabled: !props.showRightButton }"
				@click="$emit('shiftRight')"
			/>
		</div>
		<!-- Row 3 -->
		<div class="d-flex align-items-center" :class="row3layout">
			<!-- Settings button -->
			<span v-if="editmode == 1" type="button" class="p-1" @click="toggleEdit">
				<span class="fa-solid fa-xl fa-gear" />
			</span>
			<!-- Down Button -->
			<span
				v-if="editmode == 1"
				id="graphLeftButton"
				type="button"
				class="arrowButton fa-solid fa-xl fa-chevron-circle-down p-1"
				:class="{ disabled: !props.showLeftButton }"
				@click="$emit('shiftDown')"
			/>
			<!-- Close Button -->
			<span v-if="editmode > 0" type="button" class="p-1" @click="editmode = 0">
				<span class="fa-solid fa-xl fa-circle-check" />
			</span>
		</div>
	</div>
</template>

<script setup lang="ts">
import { formatMonth } from '@/assets/js/helpers'
import { computed, ref } from 'vue'
import DateInput from '../shared/DateInput.vue'
import RadioBarInput from '../shared/RadioBarInput.vue'
import {
	dayGraph,
	graphData,
	initGraph,
	liveGraph,
	setGraphDate,
	yearGraph,
} from './model'
import { monthGraph } from './model'

const props = defineProps<{
	widgetid: string
	showLeftButton: boolean
	showRightButton: boolean
	ignoreLive: boolean
}>()
defineEmits(['shiftLeft', 'shiftRight', 'shiftUp', 'shiftDown'])
const editmode = ref(0)
const displayDate = computed(() => {
	if (graphData.waitForData) {
		return 'Lädt'
	} else {
		switch (graphData.graphMode) {
			case 'live':
				/* 	if (graphData.data.length) {
				const startTime = graphData.data[0].date
				const endTime = graphData.data[graphData.data.length - 1].date
				const liveGraphMinutes = Math.round((endTime - startTime) / 60000)
				return liveGraphMinutes + ' min'
			} else {
				console.warn('Graph Data empty.')
				return '???'
			} */
				return props.ignoreLive ? 'heute' : `${liveGraph.duration} min`
			case 'today':
				return 'heute'
			case 'day':
				return (
					dayGraph.date.getDate() + '.' + (dayGraph.date.getMonth() + 1) + '.'
				)
			case 'month':
				return formatMonth(monthGraph.month - 1, monthGraph.year)
			case 'year':
				return yearGraph.year.toString()
			default:
				return '???'
		}
	}
})
const graphmodes = ['live', 'today', 'day', 'month', 'year']
const modenames = ['Live', 'Heute', 'Tag', 'Monat', 'Jahr']

const gmode = computed({
	get() {
		return graphData.graphMode
	},
	set(value: string) {
		switch (value) {
			case 'day':
				dayButtonClicked()
				break
			case 'today':
				todayButtonClicked()
				break
			case 'live':
				liveButtonClicked()
				break
			case 'month':
				monthButtonClicked()
				break
			case 'year':
				yearButtonClicked()
		}
	},
})
const graphdate = computed(() => {
	switch (graphData.graphMode) {
		case 'live':
		case 'today':
			return dayGraph.getDate()
		case 'month':
			return monthGraph.getDate()
		default:
			return dayGraph.getDate()
	}
})
function setDate(v: Date) {
	setGraphDate(v)
}
function toggleEdit() {
	editmode.value += 1
	if (editmode.value > 2) {
		editmode.value = 0
	}
}
function liveButtonClicked() {
	if (graphData.graphMode != 'live') {
		graphData.graphMode = 'live'
		initGraph()
	}
}
function dayButtonClicked() {
	if (graphData.graphMode != 'day' && graphData.graphMode != 'today') {
		graphData.graphMode = 'day'
		initGraph()
	}
}
function todayButtonClicked() {
	if (graphData.graphMode != 'today') {
		graphData.graphMode = 'today'
		setGraphDate(new Date())
		initGraph()
	}
}
function monthButtonClicked() {
	if (graphData.graphMode != 'month') {
		graphData.graphMode = 'month'
		initGraph()
	}
}
function yearButtonClicked() {
	if (graphData.graphMode != 'year') {
		graphData.graphMode = 'year'
		initGraph()
	}
}
const selectorstyle = computed(() => {
	if (editmode.value > 0) {
		return { border: '1px solid var(--color-frame)' }
	} else {
		return ''
	}
})
const row3layout = computed(() => {
	if (editmode.value == 1) {
		return 'justify-content-between'
	} else {
		return 'justify-content-end'
	}
})
const row2layout = computed(() => {
	if (editmode.value == 1) {
		return 'justify-content-between'
	} else {
		return 'justify-content-center'
	}
})
</script>

<style scoped>
.rounded-pill {
	background-color: var(--color-menu);
}
.arrowButton {
	border: 0;
}
.datebadge {
	background-color: var(--color-bg);
	color: var(--color-menu);
	border: 1px solid var(--color-menu);
	font-size: var(--font-small);
	font-weight: normal;
}
.arrowButton {
	color: var(--color-menu);
}
</style>
