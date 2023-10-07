<template>
  <tr class="tablerow">
    <!-- Column 1: CP Name and flags-->
    <td class="tablecell left" @click="toggleConfig">
      <div class="d-flex flex-wrap">
        <span>
          <i :class="statusIcon" class="me-1" :style="statusColor"></i>
          <span class="me-1" :style="nameCellStyle()">
            {{ chargepoint.name }}</span
          >
        </span>
        <span
          ><i v-if="chargepoint.hasPriority" class="fa-solid fa-xs fa-star">
          </i>
          <i
            v-if="chargepoint.scheduledCharging"
            class="fa-solid fa-xs fa-clock"
          >
          </i>
        </span>
      </div>
    </td>
    <!-- Column 2: Vehicle, SoC-->
    <td class="tablecell left">
      <div class="d-flex flex-column">
        <span >{{
          chargepoint.vehicleName
        }}</span>
        <span v-if="chargepoint.isSocConfigured" class="flex-wrap">
          <BatterySymbol class="me-1" :soc="chargepoint.soc"></BatterySymbol>
          <i
            v-if="chargepoint.isSocManual"
            class="fa-solid fa-sm fas fa-edit me-2"
            :style="{ color: 'var(--color-menu)' }"
          ></i>
          <i
            v-if="!chargepoint.isSocManual"
            class="fa-solid fa-sm fa-sync me-2"
            :style="{ color: 'var(--color-menu)' }"
          ></i>
        </span>
      </div>
    </td>
    <!-- Column 3: Mode, Power -->
    <td class="tablecell left" 
    data-bs-toggle="modal"
        :data-bs-target="'#cpsconfig-' + chargepoint.id"
        >
      <div class="d-flex flex-column">
        <span class="d-flex align-items-center flex-wrap">
          <span>{{ chargePowerString }}</span>

          <span class="d-flex align-items-center me-1">
            <span class="badge phasesInUse rounded-pill">
              {{ chargePhasesString }}</span
            >
            <span>
              {{ chargeAmpereString }}
            </span>
          </span>
        </span>
        <span :style="modeStyle" >
          <i class="fa me-1" :class="modeIcon"> </i> {{ modeString }}
        </span>
      </div>
    </td>
    <!-- Column 4: Energy, Range -->
    <td class="tablecell left" 
    data-bs-toggle="modal"
        :data-bs-target="'#cpsconfig-' + chargepoint.id">
        <div class="d-flex flex-column">
        <span class="me-2">{{ chargeEnergyString }}</span>
        <span >{{
          chargedRangeString
        }}</span>
      </div>
    </td>

    <td class="buttoncell right">
      <span
        class="fa-solid fa-lg fa-edit ps-1 tableicon"
        data-bs-toggle="modal"
        :data-bs-target="'#cpsconfig-' + chargepoint.id"
      ></span>
    </td>
  </tr>
  <tr v-if="showConfig">
    <td colspan="5" class="px-0">
      <CPChargeConfigPanel
        :chargepoint="chargepoint"
        v-if="showConfig"
        v-on:closeConfig="toggleConfig"
      >
      </CPChargeConfigPanel>
    </td>
  </tr>
</template>

<script setup lang="ts">
import { ref, computed } from 'vue'
import type { ChargePoint } from '../model'
import { chargemodes, globalConfig } from '@/assets/js/themeConfig'
import { formatWatt, formatWattH } from '@/assets/js/helpers'
import CPChargeConfigPanel from '../cpConfig/CPChargeConfigPanel.vue'
import BatterySymbol from '../../shared/BatterySymbol.vue'
const props = defineProps<{
  chargepoint: ChargePoint
}>()
const phaseSymbols = ['/', '\u2460', '\u2461', '\u2462']
const showConfig = ref(false)
const modeIcon = computed(() => {
  return chargemodes[props.chargepoint.chargeMode].icon
})
const statusIcon = computed(() => {
  let icon = ''
  if (props.chargepoint.isLocked) {
    icon = 'fa-lock'
  } else if (props.chargepoint.isCharging) {
    icon = ' fa-bolt'
  } else if (props.chargepoint.isPluggedIn) {
    icon = 'fa-plug'
  }
  return 'fa ' + icon
})
const statusColor = computed(() => {
  let result = { color: 'var(--color-axis)' }
  if (props.chargepoint.isLocked) {
    result.color = 'var(--color-evu)'
  } else if (props.chargepoint.isCharging) {
    result.color = 'var(--color-charging)'
  } else if (props.chargepoint.isPluggedIn) {
    result.color = 'var(--color-battery)'
  }
  return result
})
const modeStyle = computed(() => {
  switch (props.chargepoint.chargeMode) {
    case 'stop':
      return { color: 'var(--fg)' }
    default:
      return {
        color: chargemodes[props.chargepoint.chargeMode].color,
      }
  }
})
const chargePowerString = computed(() => {
  return formatWatt(props.chargepoint.power, globalConfig.decimalPlaces)
})
const chargeAmpereString = computed(() => {
  return props.chargepoint.current + ' A'
})
const chargePhasesString = computed(() => {
  return props.chargepoint.phasesInUse
})
const chargeEnergyString = computed(() => {
  if (props.chargepoint.dailyYield > 0) {
    return formatWattH(props.chargepoint.dailyYield, globalConfig.decimalPlaces)
  } else {
    return '0 Wh'
  }
})
const chargedRangeString = computed(() => {
  if (
    props.chargepoint.averageConsumption > 0 &&
    props.chargepoint.dailyYield > 0
  ) {
    return (
      '(' +
      Math.round(
        props.chargepoint.dailyYield /
          props.chargepoint.averageConsumption /
          10,
      ).toString() +
      ' km)'
    )
  } else {
    return ''
  }
})
const modeString = computed(() => {
  return chargemodes[props.chargepoint.chargeMode].name
})
function nameCellStyle() {
  return { color: props.chargepoint.color }
}
function toggleConfig() {
  showConfig.value = !showConfig.value
}
</script>

<style scoped>
.tablerow {
  margin: 14px;
}
.tablecell {
  color: var(--color-fg);
  background-color: var(--color-bg);
  text-align: center;
  padding-top: 2px;
  padding-left: 2px;
  padding-right: 2px;
  vertical-align: baseline;
  line-height: 1.4rem;
  font-size: var(--font-small);
}
.buttoncell {
  background-color: var(--color-bg);
  padding: 0;
  margin: 0;
}
.left {
  text-align: left;
}
.tablecell.right {
  text-align: right;
}
.tablecolum1 {
  color: var(--color-fg);
  text-align: left;
  margin: 0;
  padding: 0;
}
.tableicon {
  color: var(--color-menu);
}
.fa-star {
  color: var(--color-evu);
}
.fa-clock {
  color: var(--color-battery);
}
</style>
