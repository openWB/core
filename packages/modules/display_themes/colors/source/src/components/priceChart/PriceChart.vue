<template>
	<div class="pricesettings">
		<div class="grapharea">
			<p>Anbieter: {{ etData.etProvider }}</p>
			<figure id="pricechart">
				<svg viewBox="0 0 400 300">
					<g
						:id="chartId"
						:origin="draw"
						:transform="'translate(' + margin.top + ',' + margin.right + ')'"
					/>
				</svg>
			</figure>
		</div>
		<div class="controlarea">
			<span class="pt-1 pb-2 d-flex justify-content-between">
				<button
					type="button"
					class="btn btn-lg keypadbutton me-3"
					@click="showKeypad"
				>
					<i class="fa fa-xl fa-keyboard" />
				</button>
				<button
					v-if="!displayKeypad"
					type="button"
					class="btn btn-lg confirmbutton"
					:style="confirmButtonStyle"
					data-bs-dismiss="modal"
					@click="setMaxPrice"
				>
					Bestätigen
				</button>
			</span>
			<PricePad
				v-if="displayKeypad"
				v-model="maxTyped"
				:decimals="1"
				class="mb-3"
			/>

			<!-- <div class="grid12 pb-5">
					<ConfigItem
						title="Strompreisbasiert laden"
						icon="fa-coins"
						iconcolor="var(--color-battery)"
					>
						<SwitchInput v-model="etActive"></SwitchInput>
					</ConfigItem>
				</div> -->
			<div v-else class="sliderarea">
				<RangeInput
					id="etmaxprice"
					v-model="maxPrice"
					:min="Math.floor(prices[0] - 1)"
					:max="Math.ceil(prices[prices.length - 1] + 1)"
					:step="0.1"
					:decimals="1"
					:show-subrange="true"
					:subrange-min="prices[0]"
					:subrange-max="prices[prices.length - 1]"
					unit="ct"
				/>
				<div class="d-flex justify-content-between pb-2 pt-0 mt-0">
					<button type="button" class="btn jumpbutton" @click="priceDown">
						<i class="fa fa-xl fa-arrow-left" />
					</button>
					<button type="button" class="btn jumpbutton" @click="priceUp">
						<i class="fa fa-xl fa-arrow-right" />
					</button>
				</div>
			</div>

			<!-- <span class="pt-3" @click="showKeypad">
					<button
						type="button"
						class="btn btn-lg btn-secondary"
						:style="confirmButtonStyle"
					>
						Keypad
					</button>
				</span> -->
		</div>
	</div>
</template>

<script setup lang="ts">
import { computed, onMounted, ref } from 'vue'
import { etData } from './model'
import {
	extent,
	scaleTime,
	scaleLinear,
	line,
	axisBottom,
	timeFormat,
	axisLeft,
	select,
} from 'd3'
import RangeInput from '../shared/RangeInput.vue'
//import ConfigItem from '../shared/ConfigItem.vue'
//import SwitchInput from '../shared/SwitchInput.vue'
import { chargePoints } from '../chargePointList/model'
import PricePad from '../shared/PricePad.vue'

const props = defineProps<{
	chargePointId: number
	globalview?: boolean
}>()
const cp = computed(() => chargePoints[props.chargePointId])
const maxPriceEdited = ref(false)
const displayKeypad = ref(false)
/* const etActive = computed({
	get: () => cp.value.etActive,
	set: (value: boolean) => {
		cp.value.etActive = value
	},
}) */
let _maxPrice = cp.value ? ref(cp.value.etMaxPrice) : ref(0)
const maxPrice = computed({
	get() {
		return _maxPrice.value
		// ref(props.chargepoint.etMaxPrice)
	},
	set(newmax) {
		_maxPrice.value = newmax
		maxPriceEdited.value = true
	},
})

const maxTyped = computed({
	get() {
		return (Math.round(_maxPrice.value * 10) / 10).toString()
	},
	set(newmax) {
		maxPrice.value = parseFloat(newmax) ?? maxPrice.value
		displayKeypad.value = false
	},
})
function setMaxPrice() {
	if (cp.value) {
		cp.value.etMaxPrice = maxPrice.value
	}
	maxPriceEdited.value = false
}
const needsUpdate = ref(false)
let dummy = false
const width = 400
const height = 250
const margin = { top: 0, bottom: 15, left: 20, right: 15 }
const axisfontsize = 12

const plotdata = computed(() => {
	let valueArray: [Date, number][] = []
	if (etData.etPriceList.size > 0) {
		etData.etPriceList.forEach((value, date) => {
			valueArray.push([date, value])
		})
	}
	return valueArray
})
const barwidth = computed(() => {
	if (plotdata.value.length > 1) {
		return (width - margin.left - margin.right) / plotdata.value.length - 1
	} else {
		return 0
	}
})
const confirmButtonStyle = computed(() => {
	if (maxPriceEdited.value) {
		return { background: 'var(--color-charging)', color: 'var(--color-fg)' }
	} else {
		return { background: 'var(--color-menu)' }
	}
})
function showKeypad() {
	displayKeypad.value = !displayKeypad.value
}
const xScale = computed(() => {
	let xdomain = extent(plotdata.value, (d) => d[0]) as [Date, Date]
	if (xdomain[1]) {
		xdomain[1] = new Date(xdomain[1])
		xdomain[1].setTime(xdomain[1].getTime() + 3600000)
	}
	return scaleTime()
		.range([margin.left, width - margin.right])
		.domain(xdomain)
})
const yDomain = computed(() => {
	let yd = extent(plotdata.value, (d) => d[1]) as [number, number]
	yd[0] = yd[0] ? Math.floor(yd[0] - 1) : 0
	yd[1] = yd[1] ? Math.floor(yd[1] + 1) : 0
	return yd
})
const yScale = computed(() => {
	return scaleLinear()
		.range([height - margin.bottom, 0])
		.domain(yDomain.value)
})
const linePath = computed(() => {
	const generator = line()
	const points = [
		[margin.left, yScale.value(maxPrice.value)],
		[width - margin.right - 1, yScale.value(maxPrice.value)],
	]
	return generator(points as [number, number][])
})

const xAxisGenerator = computed(() => {
	return axisBottom<Date>(xScale.value)
		.ticks(plotdata.value.length)
		.tickSize(5)
		.tickSizeInner(-height)
		.tickFormat((d) => (d.getHours() % 6 == 0 ? timeFormat('%H:%M')(d) : ''))
})
const yAxisGenerator = computed(() => {
	return axisLeft<number>(yScale.value)
		.ticks(6)
		.tickSizeInner(-(width - margin.right - margin.left))
		.tickFormat((d) => d.toString())
})
const draw = computed(() => {
	// force a redraw if needsUpdate is true
	if (needsUpdate.value == true) {
		dummy = !dummy
	}

	const svg = select('g#' + chartId.value)
	svg.selectAll('*').remove()
	const bargroups = svg
		.selectAll('bar')
		.data(plotdata.value)
		.enter()
		.append('g')
	bargroups
		.append('rect')
		.attr('class', 'bar')
		.attr('x', (d) => xScale.value(d[0]))
		.attr('y', (d) => yScale.value(d[1]))
		.attr('width', barwidth.value)
		.attr('height', (d) => yScale.value(yDomain.value[0]) - yScale.value(d[1]))
		.attr('fill', (d) =>
			d[1] <= maxPrice.value ? 'var(--color-charging)' : 'var(--color-axis)',
		)
	// X Axis
	const xAxis = svg.append('g').attr('class', 'axis').call(xAxisGenerator.value)
	xAxis.attr('transform', 'translate(0,' + (height - margin.bottom) + ')')
	xAxis
		.selectAll('.tick')
		.attr('font-size', axisfontsize)
		.attr('color', 'var(--color-bg)')
	xAxis
		.selectAll('.tick line')
		.attr('stroke', 'var(--color-bg)')
		.attr('stroke-width', (d) =>
			(d as Date).getHours() % 6 == 0 ? '2' : '0.5',
		)
	xAxis.select('.domain').attr('stroke', 'var(--color-bg')
	// Y Axis
	const yAxis = svg.append('g').attr('class', 'axis').call(yAxisGenerator.value)
	yAxis.attr('transform', 'translate(' + margin.left + ',' + 0 + ')')
	yAxis
		.selectAll('.tick')
		.attr('font-size', axisfontsize)
		.attr('color', 'var(--color-bg)')

	yAxis
		.selectAll('.tick line')
		.attr('stroke', 'var(--color-bg)')
		.attr('stroke-width', (d) => ((d as number) % 5 == 0 ? '2' : '0.5'))
	yAxis.select('.domain').attr('stroke', 'var(--color-bg)')
	// zero line

	// Line for max price
	svg.append('path').attr('d', linePath.value).attr('stroke', 'yellow')

	return 'PriceChart.vue'
})
const chartId = computed(() => {
	if (cp.value) {
		return 'priceChartCanvas' + cp.value.id
	} else {
		return 'priceChartCanvasGlobal'
	}
})
const prices = computed(() => {
	let result: number[] = []
	etData.etPriceList.forEach((p) => {
		result.push(p)
	})
	return result.sort((a, b) => a - b)
})

function priceDown() {
	let lastValue = prices.value[0]
	for (let p of prices.value) {
		if (p >= maxPrice.value) {
			break
		} else {
			lastValue = p
		}
	}
	maxPrice.value = lastValue
}
function priceUp() {
	let result = prices.value[0]
	for (let p of prices.value) {
		if (p > maxPrice.value) {
			result = p
			break
		} else {
			result = p
		}
	}
	maxPrice.value = result
}

onMounted(() => {
	needsUpdate.value = !needsUpdate.value
})
</script>
<style scoped>
.pricesettings {
	display: grid;
	grid-template-columns: 50% 50%;
	grid-template-rows: 340px;
}
.grapharea {
	display: flex;
	flex-direction: column;
	justify-content: space-between;
	align-items: stretch;
	min-width: 0px;
	overflow: hidden;
	height: 100%;
}
.controlarea {
	display: flex;
	flex-direction: column;
	justify-content: space-between;
	align-items: stretch;
	min-width: 0px;
	overflow: hidden;
	height: 100%;
	padding-left: 20px;
	padding-right: 10px;
}
.sliderarea {
	margin-bottom: 45px;
}
.subtitle {
	font-size: var(--font-settings);
	font-weight: regular;
}
.priceinput {
	width: 100%;
}

.color-charging {
	color: var(--color-charging);
}

.fa-circle-check {
	color: var(--color-menu);
}

.settingsheader {
	color: var(--color-charging);
	font-size: 16px;
	font-weight: bold;
}

.providername {
	color: var(--color-axis);
	font-size: 16px;
}
.confirmbutton {
	background-color: var(--color-charging);
	color: var;
}
.keypadbutton {
	background-color: var(--color-menu);
}

.jumpbutton {
	background-color: var(--color-menu);
	color: var(--color-bg);
	border: 0;
}
</style>
