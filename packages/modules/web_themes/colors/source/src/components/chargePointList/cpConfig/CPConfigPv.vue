<template>
  <div class="pt-2">
    <p class="heading ms-1">
      PV-Laden:
    </p>

    <!-- Maximum SoC -->
    <ConfigItem title="Maximaler Ladestand" icon="fa-battery-three-quarters" :fullwidth="true">
      <RangeInput
        id="maxSoc"
        :min="0"
        :max="100"
        :step="1"
        unit="%"
        v-model="cp.pvMaxSoc"
      ></RangeInput>
    </ConfigItem>
    <ConfigItem title="Einspeisegrenze beachten" icon="fa-hand" :fullwidth="true">
      <div class="form-check form-switch">
        <input
          class="form-check-input"
          type="checkbox"
          role="switch"
          id="feedInLimitSwitch"
          v-model="cp.pvFeedInLimit"
        />
      </div>
    </ConfigItem>
    <hr/>
    <!-- Min-PV-Laden -->
    <ConfigItem title="Min-SoC-Laden" icon="fa-battery-half" :infotext="infotext['minsoc']" :fullwidth="true">
      <SwitchInput v-model="useMinSoc"></SwitchInput> 
    </ConfigItem>
    
    <!-- Minimum SoC -->
    <ConfigItem title="...bis SoC" v-if="useMinSoc" :fullwidth="true">
      <template v-slot:info>{{ infotext['minsoc'] }}</template>
        <RangeInput
        id="minSoc"
        :min="0"
        :max="100"
        :step="1"
        unit="%"
        v-model="cp.pvMinSoc"
      ></RangeInput>
    </ConfigItem>
    <!-- Minimum Soc Current -->
    <ConfigItem title="...mit Ladestrom" v-if="useMinSoc" :fullwidth="true">
      <RangeInput
        id="minSocCurrent"
        :min="6"
        :max="32"
        :step="1"
        unit="A"
        v-model="cp.pvMinSocCurrent"
      ></RangeInput>
    </ConfigItem>
    <hr v-if="useMinPv || useMinSoc"/>
    
    <!-- Min+PV-Laden -->
    <ConfigItem title="Min+PV-Laden" icon="fa-bolt" :infotext="infotext['minpv']" :fullwidth="true">
      <SwitchInput v-model="useMinPv"></SwitchInput> 
    </ConfigItem>
     <!-- Minimum Current -->
    <ConfigItem title="...bei Ladestrom (minimal)" v-if="useMinPv" :fullwidth="true">
      <RangeInput
        id="minCurrent"
        :min="6"
        :max="32"
        :step="1"
        unit="A"
        v-model="cp.pvMinCurrent"
      ></RangeInput>
      
    </ConfigItem>
    
  </div>
</template>

<script setup lang="ts">
import { ref, computed } from 'vue'
import type { ChargePoint } from '../model'
import ConfigItem from '../../shared/ConfigItem.vue'
import RangeInput from '@/components/shared/RangeInput.vue'
import SwitchInput from '@/components/shared/SwitchInput.vue'
import { infotext } from '@/assets/js/themeConfig'
const props = defineProps<{
  chargepoint: ChargePoint
}>()
const cp = ref(props.chargepoint)

// methods:

// computed
const chargeTemplateId = computed(() => {
  console.log(cp.value)
  return cp.value.chargeTemplate
})
const useMinPv = computed({
  get() {
    return (cp.value.pvMinCurrent > 5)
  },
  set (v: boolean) {
    if (!v) {
      cp.value.pvMinCurrent = 0
    } else {
      cp.value.pvMinCurrent = 6
    }
  }
})
const useMinSoc = computed({
  get() {
    return (cp.value.pvMinSoc > 0)
  },
  set (v:boolean) {
    if (v) {
      cp.value.pvMinSoc = 50
  } else {
    cp.value.pvMinSoc = 0
  }
  }
})
</script>

<style scoped>
.chargeConfigSelect {
  background: var(--color-bg);
  color: var(--color-fg);
}
.heading {
  color: var(--color-pv);
}
</style>
