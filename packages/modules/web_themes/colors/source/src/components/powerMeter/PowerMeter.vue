<template>
  <WBWidget :full-width="true">
    <template v-slot:title>Aktuelle Leistung</template>
    <!-- <template v-slot:buttons>
      <button class="btn btn-outline-secondary btn-sm" data-bs-toggle="modal" data-bs-target="#themeconfig">
      <span class="fa-solid fa-bars px-0"></span>
    </button>
      </template> -->
    <figure id="powermeter" class="p-0 m-0">
      <svg :viewBox="'0 0 ' + width + ' ' + height">
        <g :transform="'translate(' + width / 2 + ',' + height / 2 + ')'">
          <!-- Show the two arcs -->
          <PMSourceArc
            :radius="radius"
            :cornerRadius="cornerRadius"
            :circleGapSize="circleGapSize"
            :emptyPower="emptyPower"
          ></PMSourceArc>

          <PMUsageArc
            :usageSummary="usageSummary"
            :shDevice="shDevices"
            :radius="radius"
            :cornerRadius="cornerRadius"
            :circleGapSize="circleGapSize"
            :emptyPower="emptyPower"
          ></PMUsageArc>

          <!-- Show the values for the different categories -->
          <PMLabel
            :x="0"
            :y="(-height) / 5"
            :data="sourceSummary.pv"
            :props="masterData.pv"
            :anchor="'middle'"
            :config="globalConfig"
          />
          <PMLabel
            :x="0"
            :y="(-height) / 2 * 3 / 5"
            :data="sourceSummary.evuIn"
            :props="masterData.evuIn"
            :anchor="'middle'"
            :config="globalConfig"
          />
          <PMLabel
            :x="(-height) / 2 / 5"
            :y="height / 2 - margin + 15"
            :data="sourceSummary.batOut"
            :props="masterData.batOut"
            :anchor="'end'"
            :config="globalConfig"
          />
          <!-- iterate over all usage items-->
          <PMLabel
            v-for="(item,index) in valuesToDisplay"
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
            v-if="chargepoints.length > 0 && chargepoints[0].isSocConfigured"
            :x="-width / 2 - margin / 4 + 10"
            :y="-height / 2 + margin + 5"
            :labeltext="trimName(chargepoints[0].vehicleName) + ': ' + soc(0) + '%'"
            :labelcolor="chargepoints[0].color"
            :anchor="'start'"
            :config="globalConfig"
          />
          <PMLabel
            v-if="chargepoints.length > 1 && chargepoints[1].isSocConfigured"
            :x="width / 2 + margin / 4 - 10"
            :y="-height / 2 + margin + 5"
            :labeltext="trimName(chargepoints[1].vehicleName) + ': ' + soc(1) + '%'"
            :labelcolor="chargepoints[1].color"
            :anchor="'end'"
            :config="globalConfig"
          />
          <!-- Show the SoC of the 1st battery -->
          <PMLabel
            v-if="globalData.batterySoc > 0"
            :x="-width / 2 - margin / 4 + 10"
            :y="height / 2 - margin + 15"
            :labeltext="'Speicher: ' + globalData.batterySoc + '%'"
            :labelcolor="usageSummary.batIn.color"
            :anchor="'start'"
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
import { globalData, shDevices, sourceSummary, usageSummary, masterData } from '@/assets/js/model'
import { chargePoints, vehicles } from '@/components/chargePointList/model'
import PMSourceArc from './PMSourceArc.vue';
import PMUsageArc from './PMUsageArc.vue'
import PMLabel from "./PMLabel.vue";
import WBWidget from "../shared/WBWidget.vue";
import { formatWatt } from "@/assets/js/helpers";
import ModalComponent from "../shared/ModalComponent.vue";
import ThemeSettings from "../../views/ThemeSettings.vue";

// state:
const width = 500
const height = width
const margin = 20
const cornerRadius = 1
const circleGapSize = Math.PI / 40
const schemes = [[4], [4, 6], [1, 4, 6], [0, 2, 4, 6], [0, 2, 3, 5, 6]]
  

// computed

const labelPositions = [{ x: -85, y: height / 2 * 1 / 5 },
		{ x: 0, y: height / 2 * 1 / 5 },
		{ x: 85, y: height / 2 * 1 / 5 },
		{ x: -85, y: height / 2 * 2 / 5 },
		{ x: 0, y: height / 2 * 2 / 5 },
		{ x: 85, y: height / 2 * 2 / 5 },
		{ x: 0, y: height / 2 * 3 / 5 },
		]
const radius = computed(() => {
  return width / 2 - margin;
})
const currentConsumptionString = computed(() => {
  let consumptionLabel = ''
  let sourcesToDisplay = Object.values(sourceSummary).filter(v => (v.power > 0))
	if ((sourcesToDisplay.length == 1) && (sourcesToDisplay[0].name == 'PV')) {
			consumptionLabel = "Aktueller Verbrauch: "
		} else {
			consumptionLabel = "Bezug/Verbrauch: "
		}

  return ( consumptionLabel + formatWatt(
    usageSummary.house.power +
    usageSummary.charging.power +
    usageSummary.devices.power +
    usageSummary.batIn.power,
    globalConfig.decimalPlaces
  ))
})
const maxPowerString = computed(() => {
  let currentPower =
    sourceSummary.pv.power +
    sourceSummary.evuIn.power +
    sourceSummary.batOut.power;
  return globalConfig.maxPower > currentPower
    ? formatWatt(globalConfig.maxPower, globalConfig.decimalPlaces)
    : formatWatt(currentPower, globalConfig.decimalPlaces);
})
const chargepoints  = computed(() => {
  return Object.values(chargePoints);
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
  return [usageSummary.evuOut,
  usageSummary.charging,
  usageSummary.devices,
  usageSummary.batIn,
  usageSummary.house]
    .filter(x => (x.power > 0))
})
const scheme = computed(() =>  schemes[valuesToDisplay.value.length - 1])
function labelCoordinates (item: number) {
  return labelPositions[scheme.value[item]]
}


// methods
function resetArcs() {
  let maxPower =
    sourceSummary.pv.power +
    sourceSummary.evuIn.power +
    sourceSummary.batOut.power;

    globalConfig.maxPower = maxPower
}
function soc(i: number) {
  return chargepoints.value[i].soc
}
function trimName(name: string) {
  const maxlen = 12
  return (name.length > maxlen) ? name.slice(0, maxlen-1) + '.': name  
}

</script>

<style></style>
