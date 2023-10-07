/* * BbChargeButton.vue * colors theme for openwb 2.0 * Copyright (c) 2022 Claus
Hagen */

<template>
  <div class="col-lg-4 p-0 m-0 mt-1">
    <div class="d-grid gap-2">
      <button
        type="button"
        class="btn mx-1 mb-0 p-1 regularTextSize chargeButton shadow"
        :style="buttonStyle"
        data-bs-toggle="modal"
        :data-bs-target="'#' + modalId"
      >
        <div class="m-0 p-0">
          <div class="m-0 p-0 d-flex justify-content-between">
            
            <!-- Status indicator -->
            <div class="m-0 p-0 d-flex flex-column left ">
              <span
                v-if="chargepoint.isPluggedIn"
                class="mx-1 badge rounded-pill smallTextSize plugIndicator"
              >
                <i :class="plugPillClass"></i>
                <span v-if="chargepoint.isCharging" class="ms-2">
                  {{ formatWatt(chargepoint.power) }}
                </span>
              </span>
              <span
                v-if="!chargepoint.isPluggedIn"
                class="mx-1 badge rounded-pill smallTextSize plugIndicator"
              >
                <i :class="plugPillClass"></i>
                <span v-if="chargepoint.isCharging" class="ms-2">
                  {{ formatWatt(chargepoint.power) }}
                </span>
              </span>
            </div>
            <!-- Chargepoint name -->
            <div class="m-0 p-0 d-flex flex-column center" >{{ chargepoint.name }}</div>
            <!-- Mode indicator -->
            <div class="m-0 p-0 d-flex flex-column right">
              <span
                class="mx-2 badge rounded-pill smallTextSize modeIndicator"
                :style="modePillStyle"
              >
                <i class="fa me-1" :class="modeIcon"></i>
                {{ modeString }}
                <!-- PV priority -->
                <span
                  v-if="
                    chargepoint.chargeMode == ChargeMode.pv_charging &&
                    globalData.isBatteryConfigured
                  "
                  class="ps-1"
                >
                  (
                  <i class="fa m-0" :class="priorityIcon"></i>)
                </span>
              </span>
            </div>
          </div>
          </div>
        
      </button>
    </div>
    <ModalComponent :modalId="modalId">
      <template v-slot:title>Lademodus für {{ chargepoint.name }}</template>
      <BBSelect :cpId="chargepoint.id"></BBSelect>
    </ModalComponent>
  </div>
</template>

<script setup lang="ts">
import { globalData } from '@/assets/js/model'
import { ChargePoint, ChargeMode } from '@/components/chargePointList/model'
import { chargemodes } from '@/assets/js/themeConfig'
import { computed } from 'vue'
import { formatWatt } from '@/assets/js/helpers'
import BBSelect from './BBSelect.vue'
import ModalComponent from '@/components/shared/ModalComponent.vue'

//props
const props = defineProps<{
  chargepoint: ChargePoint
}>()
const modalId = 'chargeSelectModal' + props.chargepoint.id
const modeString = computed(() => {
  return chargemodes[props.chargepoint.chargeMode].name
})
const buttonStyle = computed(() => {
  let style = {
    background: 'var(--color-menu)',
  }
  if (props.chargepoint.isLocked) {
    style.background = 'var(--color-evu)'
  } else if (props.chargepoint.isCharging) {
    style.background = 'var(--color-charging)'
  } else if (props.chargepoint.isPluggedIn) {
    style.background = 'var(--color-battery)'
  }
  return style
})
interface buttonStyle {
  background: string
  color: string
}
const modePillStyle = computed(() => {
  if (chargemodes) {
    let style = {
      background: chargemodes[props.chargepoint.chargeMode].color,
      color: 'white',
    }

    switch (props.chargepoint.chargeMode) {
      case ChargeMode.instant_charging:
        if (props.chargepoint.isCharging && !props.chargepoint.isLocked) {
          style = swapcolors(style)
        }
        break
      case ChargeMode.standby:
      case ChargeMode.stop:
        if (!props.chargepoint.isPluggedIn) {
          style = swapcolors(style)
        }
        break
      case ChargeMode.scheduled_charging:
        if (
          props.chargepoint.isPluggedIn &&
          !props.chargepoint.isCharging &&
          !props.chargepoint.isLocked
        ) {
          style = swapcolors(style)
        }
        break
      default:
        break
    }
    return style
  }
})
const modeIcon = computed(() => {
  if (chargemodes) {
    return chargemodes[props.chargepoint.chargeMode].icon
  }
})
const priorityIcon = computed(() => {
  if (globalData.pvBatteryPriority) {
    return 'fa-car-battery'
  } else {
    return 'fa-car'
  }
})
const plugPillClass = computed(() => {
  let icon = 'fa-ellipsis'
  if (props.chargepoint.isLocked) {
    icon = 'fa-lock'
  } else if (props.chargepoint.isCharging) {
    icon = ' fa-bolt'
  } else if (props.chargepoint.isPluggedIn) {
    icon = 'fa-plug'
  } 
  
  return 'fa ' + icon
})

// methods
function swapcolors(style: buttonStyle): buttonStyle {
  let c = style.color
  style.color = style.background
  style.background = c
  return style
}
</script>

<style scoped>
.plugIndicator {
  color: white;
  border: 1px solid white;
  
}

.chargeButton {
  color: white;
}
.left {
  float: left;
  
}
.right {
  float:right;
  

}
.center {
  margin:auto;
}
</style>
