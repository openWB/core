<template>
	<WBWidget :full-width="true">
		<template #title> Aktuelle Leistung </template>
		<figure id="powermeter" class="p-0 m-0">
			<svg :viewBox="'0 0 ' + width + ' ' + height">
				<g :transform="'translate(' + width / 2 + ',' + height / 2 + ')'">
					<!-- Show the two arcs -->
					<PMSourceArc
						:radius="radius"
						:corner-radius="cornerRadius"
						:circle-gap-size="circleGapSize"
						:empty-power="emptyPower"
					/>

					<PMUsageArc
						:sh-device="shDevices"
						:radius="radius"
						:corner-radius="cornerRadius"
						:circle-gap-size="circleGapSize"
						:empty-power="emptyPower"
					/>

					<!-- Show the values for the different categories -->
					<PMLabel
						:x="0"
						:y="(-height / 10) * 2"
						:data="sourceSummary.pv"
						:props="masterData.pv"
						:anchor="'middle'"
						:config="globalConfig"
					/>
					<PMLabel
						:x="0"
						:y="(-height / 10) * 3"
						:data="sourceSummary.evuIn"
						:props="masterData.evuIn"
						:anchor="'middle'"
						:config="globalConfig"
					/>
					<PMLabel
						:x="0"
						:y="-height / 10"
						:data="sourceSummary.batOut"
						:props="masterData.batOut"
						:anchor="'middle'"
						:config="globalConfig"
					/>
					<PMLabel
						v-if="etData.active"
						:x="0"
						:y="-height / 10"
						:data="sourceSummary.batOut"
						:props="masterData.batOut"
						:anchor="'middle'"
						:config="globalConfig"
					/>
					<!-- iterate over all usage items-->
					<PMLabel
						v-for="(item, index) in valuesToDisplay"
						:key="index"
						:x="labelCoordinates(index).x"
						:y="labelCoordinates(index).y"
						:data="item"
						:labelicon="item.icon"
						:labelcolor="item.color"
						:anchor="'middle'"
						:config="globalConfig"
					/>

					<!-- Show the SoC for the first two cars -->
					<PMLabel
						v-if="
							topVehicles[0] != undefined &&
							vehicles[topVehicles[0]] != undefined
						"
						:x="-width / 2 - margin / 4 + 10"
						:y="-height / 2 + margin + 5"
						:labeltext="
							trimName(vehicles[topVehicles[0]].name) +
							': ' +
							Math.round(vehicles[topVehicles[0]].soc) +
							'%'
						"
						:labelcolor="chargepoints[0].color"
						:anchor="'start'"
						:config="globalConfig"
					/>
					<PMLabel
						v-if="
							topVehicles[1] != undefined &&
							vehicles[topVehicles[1]] != undefined
						"
						:x="width / 2 + margin / 4 - 10"
						:y="-height / 2 + margin + 5"
						:labeltext="
							trimName(vehicles[topVehicles[1]].name) +
							': ' +
							Math.round(vehicles[topVehicles[1]].soc) +
							'%'
						"
						:labelcolor="
							chargepoints[1] ? chargepoints[1].color : 'var(--color-charging)'
						"
						:anchor="'end'"
						:config="globalConfig"
					/>
					<!-- Show the SoC of the batteries -->
					<PMLabel
						v-if="globalData.batterySoc > 0"
						:x="-width / 2 - margin / 4 + 10"
						:y="height / 2 - margin + 15"
						:labeltext="'Speicher: ' + globalData.batterySoc + '%'"
						:labelcolor="usageSummary.batIn.color"
						:anchor="'start'"
						:config="globalConfig"
					/>
					<!-- Show the current energy price -->
					<PMLabel
						v-if="etData.active"
						:x="width / 2 + margin / 4 - 10"
						:y="height / 2 - margin + 15"
						:value="currentPrice"
						:labeltext="etData.etCurrentPriceString"
						labelcolor="var(--color-charging)"
						:anchor="'end'"
						:config="globalConfig"
					/>
					<!-- Show the current consumption -->
					<PMLabel
						:x="0"
						:y="0"
						:labeltext="currentConsumptionString"
						labelcolor="var(--color-fg)"
						anchor="middle"
						:config="globalConfig"
					/>
					<!-- Show the Peak value if we use relative arc lengths -->
					<text
						v-if="globalConfig.showRelativeArcs"
						:x="width / 2 - 44"
						y="2"
						text-anchor="middle"
						fill="var(--color-axis)"
						font-size="12"
					>
						Peak: {{ maxPowerString }}
					</text>
				</g>
			</svg>
		</figure>
		<!-- <ModalComponent modal-id="themeconfig">
			<template v-slot:title>Look & Feel</template>
			<ThemeSettings @resetArcs="resetArcs"></ThemeSettings>
		</ModalComponent> -->
	</WBWidget>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import { globalConfig } from '@/assets/js/themeConfig'
import {
	globalData,
	sourceSummary,
	usageSummary,
	masterData,
} from '@/assets/js/model'
import { shDevices } from '../smartHome/model'
import {
	chargePoints,
	vehicles,
	topVehicles,
} from '@/components/chargePointList/model'
import PMSourceArc from './PMSourceArc.vue'
import PMUsageArc from './PMUsageArc.vue'
import PMLabel from './PMLabel.vue'
import WBWidget from '../shared/WBWidget.vue'
import { formatWatt } from '@/assets/js/helpers'
import { etData } from '../priceChart/model'

// state:
const width = 500
const height = width
const margin = 20
const cornerRadius = 1
const circleGapSize = Math.PI / 40
const schemes = [[4], [4, 6], [1, 4, 6], [0, 2, 4, 6], [0, 2, 3, 5, 6]]

// computed

const labelPositions = [
	{ x: -85, y: ((height / 2) * 1) / 5 },
	{ x: 0, y: ((height / 2) * 1) / 5 },
	{ x: 85, y: ((height / 2) * 1) / 5 },
	{ x: -85, y: ((height / 2) * 2) / 5 },
	{ x: 0, y: ((height / 2) * 2) / 5 },
	{ x: 85, y: ((height / 2) * 2) / 5 },
	{ x: 0, y: ((height / 2) * 3) / 5 },
]
const radius = computed(() => {
	return width / 2 - margin
})
const currentConsumptionString = computed(() => {
	let consumptionLabel = ''
	let sourcesToDisplay = Object.values(sourceSummary).filter((v) => v.power > 0)
	if (sourcesToDisplay.length == 1 && sourcesToDisplay[0].name == 'PV') {
		consumptionLabel = 'Aktueller Verbrauch: '
	} else {
		consumptionLabel = 'Bezug/Verbrauch: '
	}

	return (
		consumptionLabel +
		formatWatt(
			usageSummary.house.power +
				usageSummary.charging.power +
				usageSummary.devices.power +
				usageSummary.batIn.power,
			globalConfig.decimalPlaces,
		)
	)
})
const maxPowerString = computed(() => {
	let currentPower =
		sourceSummary.pv.power +
		sourceSummary.evuIn.power +
		sourceSummary.batOut.power
	return globalConfig.maxPower > currentPower
		? formatWatt(globalConfig.maxPower, globalConfig.decimalPlaces)
		: formatWatt(currentPower, globalConfig.decimalPlaces)
})
const chargepoints = computed(() => {
	return Object.values(chargePoints)
})
const emptyPower = computed(() => {
	// with relative arcs, this is the empty portion of the arc
	let result = 0
	if (globalConfig.showRelativeArcs) {
		result =
			globalConfig.maxPower -
			(sourceSummary.pv.power +
				sourceSummary.evuIn.power +
				sourceSummary.batOut.power)
	}
	return result < 0 ? 0 : result
})
const valuesToDisplay = computed(() => {
	return [
		usageSummary.evuOut,
		usageSummary.charging,
		usageSummary.devices,
		usageSummary.batIn,
		usageSummary.house,
	].filter((x) => x.power > 0)
})
const scheme = computed(() => schemes[valuesToDisplay.value.length - 1])
function labelCoordinates(item: number) {
	return labelPositions[scheme.value[item]]
}

// methods
function trimName(name: string) {
	const maxlen = 12
	return name.length > maxlen ? name.slice(0, maxlen - 1) + '.' : name
}
const currentPrice = computed(() => {
	const [p] = etData.etPriceList.values()
	return Math.round(p * 10) / 10
})
</script>

<style></style>
