<template>

  <WBWidget :variableWidth="true" :full-width="props.fullWidth" v-if="!configmode">
    <template v-slot:title>
      <span
        :style="cpNameStyle"
       @click="configmode=!configmode"
      >
        <span class="fas fa-charging-station">&nbsp;</span>
        {{ props.chargepoint.name }}</span
      >
    </template>

    <template v-slot:buttons>
      <span
        class="ms-2 pt-1"
        :style="modePillStyle"
        @click="configmode = !configmode"
      >
        <span class="fa-solid fa-lg ps-1 fa-ellipsis-vertical"></span>
      </span>
    </template>

    <!-- Chargepoint info -->
    <div v-if="!configmode">
      <div
        class="row m-1 mt-0 p-0"
        @click="configmode = !configmode"
        >
        <div class="col m-0 mb-1 p-0 d-flex justify-content-between">
          <!-- Status information -->
          <InfoItem heading="Status:">
            <span :style="{ color: statusColor }">
              <i :class="statusIcon"></i>
              {{ statusString }}
            </span>
          </InfoItem>

          <!-- Ladung -->
          <InfoItem heading="Geladen:">
            <FormatWattH :wattH="chargepoint.chargedSincePlugged"></FormatWattH>
          </InfoItem>
          <InfoItem heading="gel. Reichw.:">
            {{ chargedRangeString }}
          </InfoItem>
        </div>
      </div>
      <div class="row m-1 p-0" v-if="props.chargepoint.power > 0"
        @click="configmode=!configmode">
        <div class="col m-0 p-0 d-flex justify-content-between">
          <InfoItem heading="Leistung:">
            <FormatWatt :watt="props.chargepoint.power"></FormatWatt>
          </InfoItem>
          <InfoItem heading="Stromstärke:">
            {{ chargeAmpereString }}
          </InfoItem>
          <InfoItem heading="Phasen:">
            {{ props.chargepoint.phasesInUse }}
          </InfoItem>
        </div>
      </div>
      <!-- Chargemode buttons -->
      <div class="row m-0 p-1 mt-3 mb-0">
        <div class="col d-flex justify-content-center">
          <RadioBarInput
            :id="'chargemode-'+chargepoint.name"
            :options="
              Object.keys(chargemodes).map((v) => { return {
                
                text: chargemodes[v].name,
                value: v,
                color: chargemodes[v].color,
                icon: chargemodes[v].icon,
                active: (chargemodes[v].mode == chargepoint.chargeMode)
              }})
            "
            v-model="chargepoint.chargeMode"
          ></RadioBarInput>
        </div>
      </div>
    </div>
    <div v-if="configmode" class="row m-0 mt-0 p-0">
      <div class="col m-0 p-0">
        <CPChargeConfigPanel
          :chargepoint="chargepoint"
          v-if="chargepoint != undefined"
        ></CPChargeConfigPanel>
      </div>
    </div>
    <!-- Car information-->
    <template v-slot:footer>
      <div v-if="!configmode">
      <div class="row" @click="configmode=!configmode">
        <div class="col">
          <h3>
            <i class="fa-solid fa-sm fa-car me-2"> </i>
            {{ chargepoint.vehicleName }}
            <span
              v-if="chargepoint.hasPriority"
              class="me-1 fa-solid fa-xs fa-star ps-1"
            ></span>
          </h3>
        </div>
      </div>
      <div class="row m-0 p-1 pt-2 mb-3">
        <!-- Car info -->

        <div class="m-0 p-0 d-flex justify-content-between">
          <InfoItem heading="Ladestand:">
            <BatterySymbol
              v-if="chargepoint.isSocConfigured"
              :soc="soc"
              class="me-2"
            ></BatterySymbol>
            <i
              v-if="chargepoint.isSocManual"
              class="fa-solid fa-sm fas fa-edit"
              :style="{ color: 'var(--color-menu)' }"
            ></i>
            <i
              v-if="!chargepoint.isSocManual"
              class="fa-solid fa-sm fa-sync"
              :style="{ color: 'var(--color-menu)' }"
            ></i>
          </InfoItem>
         <!--  <InfoItem heading="Priorität:">
            <span
              v-if="chargepoint.hasPriority"
              class="me-1 fa-solid fa-xs fa-star ps-1"
            ></span>
            {{ props.chargepoint.hasPriority ? 'Ja' : 'Nein' }}
          </InfoItem> -->
          <InfoItem heading="Reichweite:">
            {{ ((vehicles[props.chargepoint.connectedVehicle]) ? Math.round(vehicles[1].range) : 0) }} km
          </InfoItem>
          <InfoItem heading="Zeitplan:">
            <span
              v-if="chargepoint.scheduledCharging"
              class="me-1 fa-solid fa-xs fa-clock ps-1"
            ></span>
            {{ props.chargepoint.scheduledCharging ? 'Ja' : 'Nein' }}
          </InfoItem>
        </div>
      </div>
    </div>
    </template>
  </WBWidget>
  <WbWidgetFlex v-if="configmode" :full-width="props.fullWidth">
    <template v-slot:title>
      <span
        :style="cpNameStyle"
        @click="configmode=!configmode"
      >
        <span class="fas fa-gear">&nbsp;</span>
        Einstellungen {{ props.chargepoint.name }}</span
      >
    </template>

    <template v-slot:buttons>
     
      <span
        class="ms-2 pt-1"
        :style="modePillStyle"
        @click="configmode = !configmode"
      >
        <span class="fa-solid fa-lg ps-1 fa-circle-check"></span>
      </span>
    </template>
    <CPChargeConfigPanel
          :chargepoint="chargepoint"
          v-if="chargepoint != undefined"
        ></CPChargeConfigPanel>
  </WbWidgetFlex>
</template>

<script setup lang="ts">
import { computed, ref } from 'vue'
import { type ChargePoint, vehicles } from './model'
import { chargemodes } from '@/assets/js/themeConfig'
import WBWidget from '@/components/shared/WBWidget.vue'
import InfoItem from '@/components/shared/InfoItem.vue'
import CPChargeConfigPanel from './cpConfig/CPChargeConfigPanel.vue'
import BatterySymbol from '@/components/shared/BatterySymbol.vue'
import FormatWatt from '@/components/shared/FormatWatt.vue'
import FormatWattH from '../shared/FormatWattH.vue'
import RadioBarInput from '@/components/shared/RadioBarInput.vue'
import WbWidgetFlex from '../shared/WbWidgetFlex.vue'

const props = defineProps<{
  chargepoint: ChargePoint
  fullWidth? : boolean 
}>()
// state

// computed
const chargeAmpereString = computed(() => {
  return (Math.round(props.chargepoint.current * 10)/10).toLocaleString(undefined) + ' A'
})
const chargedRangeString = computed(() => {
    return Math.round(props.chargepoint.rangeCharged).toString() + ' ' + props.chargepoint.rangeUnit
  })
const statusString = computed(() => {
  if (props.chargepoint.isLocked) {
    return 'Gesperrt'
  } else if (props.chargepoint.isCharging) {
    return 'Lädt'
  } else if (props.chargepoint.isPluggedIn) {
    return 'Bereit'
  } else {
    return 'Frei'
  }
})
const statusColor = computed(() => {
  if (props.chargepoint.isLocked) {
    return 'var(--color-evu)'
  } else if (props.chargepoint.isCharging) {
    return 'var(--color-charging)'
  } else if (props.chargepoint.isPluggedIn) {
    return 'var(--color-battery)'
  } else {
    return 'var(--color-axis)'
  }
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
const modePillStyle = computed(() => {
  switch (props.chargepoint.chargeMode) {
    case 'stop':
      return { color: 'var(--fg)' }
    default:
      return {
        color: chargemodes[props.chargepoint.chargeMode].color,
      }
  }
})
const modeString = computed(() => {
  return chargemodes[props.chargepoint.chargeMode].name
})
const modeIcon = computed(() => {
  return chargemodes[props.chargepoint.chargeMode].icon
})
const soc = computed(() => {
  return props.chargepoint.soc
})
const cpNameStyle = computed(() => {
  return { color: props.chargepoint.color }
  // return { color: 'var(--color-fg)' }
})
const configmode = ref(false)

// methods
</script>

<style scoped>
.modeIndicator {
  color: white;
}
.outlinePill {
  border: 1px solid;
  background: var(--color-bg);
  vertical-align: bottom;
  font-size: var(--font-verysmall);
}
.statusIndicator {
  border: 1px solid;
  background: 'var(--bg) ';
}
.buttonIcon {
  color: var(--color-menu);
}

.fa-star {
  color: var(--color-evu);
}
.fa-clock {
  color: var(--color-battery);
}
.fa-sliders {
  color: var(--color-menu);
}

.energylabel {
  color: var(--color-menu);
}
.vehicleName {
  color: var(--color-fg);
}
.longline {
  color: var(--color-menu);
  padding: 3;
  margin-left: 5;
}
.fa-car {
  color: var(--color-menu);
}
.fa-ellipsis-vertical {
  color: var(--color-menu);
}
.fa-circle-check {
  color: var(--color-menu);
}
.heading {
  color: var(--color-menu);
  font-size: var(--font-small);
}
.content {
  font-size: var(--font-normal);
  font-weight: bold;
}
</style>
