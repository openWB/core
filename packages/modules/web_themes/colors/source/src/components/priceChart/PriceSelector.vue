<template>
	<p class="providername ms-1">Anbieter: {{ etData.etProvider }}</p>
	<PriceChart :id="`cp-${props.chargepoint?.id}`" :max-price="maxPrice" />
	<div class="chargeDuration p-0 m-0">Ladezeit: {{ charge_duration }}</div>
	<div v-if="chargepoint != undefined" class="p-3 pb-1 rangeInputContainer">
		<RangeInput
			id="pricechart_local"
			v-model="maxPrice"
			:min="Math.floor(prices[0] - 1)"
			:max="Math.ceil(prices[prices.length - 1] + 1)"
			:step="0.1"
			:decimals="2"
			:show-subrange="true"
			:subrange-min="prices[0]"
			:subrange-max="prices[prices.length - 1]"
			:unit="globalData.country == 'ch' ? 'Rp' : 'ct'"
		/>
	</div>
	<div class="d-flex justify-content-between px-3 pb-2 pt-0 mt-0">
		<button type="button" class="btn btn-sm jumpbutton" @click="priceDown">
			<i class="fa fa-sm fa-arrow-left" />
		</button>
		<button type="button" class="btn btn-sm jumpbutton" @click="priceUp">
			<i class="fa fa-sm fa-arrow-right" />
		</button>
	</div>
	<div
		v-if="chargepoint != undefined"
		class="d-flex justify-content-between align-items-center mx-2 mb-4 mt-2"
	>
		<button
			class="calculatorButton btn btn-secondary"
			type="button"
			@click="openCalculator"
		>
			Preis berechnen
		</button>

		<span class="" @click="setMaxPrice">
			<button
				type="button"
				class="btn btn-secondary confirmButton"
				:style="confirmButtonStyle"
				:disabled="!maxPriceEdited"
			>
				Bestätigen
			</button>
		</span>
	</div>

	<PriceCalculator
		:model-value="calculatedPrice"
		:cp-id="chargepoint!.id"
		@update:model-value="storePrice"
	/>
</template>

<script setup lang="ts">
import { computed, onMounted, ref } from 'vue'
import { globalData } from '@/assets/js/model'
import { etData } from './model'
import RangeInput from '../shared/RangeInput.vue'
import { chargePoints, type ChargePoint } from '../chargePointList/model'
import { Modal } from 'bootstrap'
import PriceChart from './PriceChart.vue'
import PriceCalculator from '../chargePointList/cpConfig/PriceCalculator.vue'
const props = defineProps<{
	chargepoint?: ChargePoint
	globalview?: boolean
}>()
const calculatedPrice = ref(0)
var calculatorModal = ref<Modal | null>(null)

let _maxPrice = props.chargepoint ? ref(props.chargepoint.etMaxPrice) : ref(0)
const maxPriceEdited = ref(false)
const cp = ref(props.chargepoint)
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

function setMaxPrice() {
	if (cp.value) {
		chargePoints[cp.value.id].etMaxPrice = maxPrice.value
	}
	maxPriceEdited.value = false
}
const needsUpdate = ref(false)
const confirmButtonStyle = computed(() => {
	if (maxPriceEdited.value) {
		return { background: 'var(--color-charging)' }
	} else {
		return { background: 'var(--color-menu)' }
	}
})

const prices = computed(() => {
	let result: number[] = []
	etData.etPriceList.forEach((p) => {
		result.push(p)
	})
	return result.sort((a, b) => a - b)
})

const charge_duration = computed(() => {
	const minutesPerSegment = 15
	const activeSegmentCount = prices.value.filter(
		(p) => p <= maxPrice.value,
	).length
	return `${Math.floor((activeSegmentCount * minutesPerSegment) / 60)}h ${(activeSegmentCount * minutesPerSegment) % 60}min`
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
function openCalculator() {
	const modalId = `priceCalculator-${props.chargepoint!.id}`
	calculatorModal.value = new Modal(document.getElementById(modalId)!)
	calculatorModal.value.toggle()
}
function storePrice(newPrice: number) {
	calculatorModal.value!.hide()
	maxPrice.value = newPrice
	if (cp.value) {
		chargePoints[cp.value.id].etMaxPrice = maxPrice.value
	}
	maxPriceEdited.value = false
}
onMounted(() => {
	needsUpdate.value = !needsUpdate.value
})
</script>

<style scoped>
.providername {
	color: var(--color-axis);
	font-size: 16px;
}
.jumpbutton {
	background-color: var(--color-menu);
	color: var(--color-bg);
	border: 0;
	font-size: var(--font-settings-button);
	padding-left: 12px;
	padding-right: 12px;
}
.confirmButton {
	font-size: var(--font-settings-button);
}
.chargeDuration {
	color: var(--color-charging);
	font-size: var(--font-settings);
	text-align: center;
	margin-top: -10px;
	margin-bottom: 10px;
}
.rangeInputContainer {
	font-size: var(--font-settings);
}
.calculatorButton {
	background-color: var(--color-pv);
	font-size: var(--font-settings-button);
}
</style>
