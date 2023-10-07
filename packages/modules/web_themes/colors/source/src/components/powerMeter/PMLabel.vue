<template>
<g id="pmLabel" v-if="showMe">
  <text :x="x" :y="y" :fill="color" :text-anchor = "anchor" :font-size="labelfontsize"  class="pmLabel">
      <tspan :class="textclass">{{ text }}</tspan><tspan> <FormatWatt :watt="data.power" v-if="data !== undefined"></FormatWatt></tspan>
  </text>
</g>
</template>

<script setup lang="ts">
import type { PowerItem, ItemProps } from '@/assets/js/types'
import { formatWatt } from '@/assets/js/helpers'
import { globalConfig } from '@/assets/js/themeConfig'
import FormatWatt from '../shared/FormatWatt.vue'
import { computed } from 'vue';
  
  //props 
  const props = defineProps<{
      x: number
      y: number
      data?: PowerItem
      props?: ItemProps
      anchor: string
      labeltext?: string 
      labelicon?: string
      labelcolor?: string 
  }>()

  //state
    const labelfontsize = 22
      
    // computed
      const power = computed (() => {
        return (props.data) ? formatWatt (props.data.power, globalConfig.decimalPlaces) : 0
      })
      const text = computed (() => {
        return (props.labeltext) ? props.labeltext : ((props.props) ? (props.props.icon + " ") : props.labelicon ? (props.labelicon + " ") : '')      
        })
      const color  = computed(() => {
        return (props.labelcolor) ? props.labelcolor : ((props.props) ? props.props.color : '')      
      })
      const showMe = computed (() => {
        return (!(props.data) || props.data.power > 0) 
      })
      const textclass = computed (() => {
        return (props.labeltext) ? '' : "fas"
      })
    

</script>

<style scoped>

</style>