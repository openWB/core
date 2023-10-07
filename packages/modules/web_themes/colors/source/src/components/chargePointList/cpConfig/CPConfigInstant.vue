<template>
  <div class="mt-2">
    <p class="heading ms-1">
      Sofortladen:
    </p>

    <!-- Ampere -->
    <ConfigItem title="Stromstärke"
    icon="fa-bolt" :fullwidth="true">
      <RangeInput
        id="targetCurrent"
        :min="6"
        :max="32"
        :step="1"
        unit="A"
        v-model="cp.instantTargetCurrent"
      ></RangeInput>
    </ConfigItem>
    <hr v-if="cp.instantChargeLimitMode != 'none'" />
    <!-- Limit Mode -->
    <ConfigItem title="Begrenzung" icon="fa-hand">
      <RadioInput
        :options="instantChargeLimitModes.map((e) => [e.name, e.id])"
        v-model="cp.instantChargeLimitMode"
      
        ></RadioInput
      >
      
    </ConfigItem>
    <!-- Max SoC -->
    <ConfigItem
      v-if="cp.instantChargeLimitMode == 'soc'"
      title="Maximaler SoC"
      icon="fa-sliders"
    >
      <RangeInput
        id="maxSoc"
        :min="0"
        :max="100"
        :step="1"
        unit="%"
        v-model="cp.instantTargetSoc"
      ></RangeInput>
    </ConfigItem>

    <!-- Max Energy -->
    <ConfigItem
      v-if="cp.instantChargeLimitMode == 'amount'"
      title="Zu ladende Energie"
      icon="fa-sliders"
    >
      <RangeInput
        id="maxEnergy"
        :min="0"
        :max="100"
        :step="1"
        unit="kWh"
        v-model="cp.instantMaxEnergy"
      ></RangeInput>
    </ConfigItem>
  </div>
</template>

<script setup lang="ts">
// import { eventBus } from '@/main.js'
import { ref, computed } from 'vue'
import type { ChargePoint } from '../model'
import ConfigItem from '../../shared/ConfigItem.vue'
import RangeInput from '@/components/shared/RangeInput.vue'
import RadioInput from '@/components/shared/RadioInput.vue'
const props = defineProps<{
  chargepoint: ChargePoint
}>()
const cp = ref(props.chargepoint)
const instantChargeLimitModes = [
  { name: 'keine', id: 'none' },
  { name: 'EV-SoC', id: 'soc' },
  { name: 'Energiemenge', id: 'amount' },
]
// methods
</script>

<style scoped>
.chargeConfigSelect {
  background: var(--color-bg);
  color: var(--color-fg);
}
.heading {
  color: var(--color-charging);
}
</style>
