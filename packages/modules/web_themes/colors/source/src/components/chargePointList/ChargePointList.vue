<template>
  <!-- <div v-if="true && !globalConfig.simpleCpList" class="p-0 m-0 d-flex align-items-stretch" :class="totalWidth"> -->
    <swiper-container v-if="!globalConfig.simpleCpList" :space-between="0" :slides-per-view="1" :pagination="{ clickable: true }"
      class="cplist m-0 p-0 swiper-chargepoints d-flex align-items-stretch" :class="totalWidth">
      <swiper-slide v-for="chargepoint in chargepointsToDisplay">
        <div :class="(widescreen) ? 'mb-0' : 'mb-5'" class="d-flex align-items-stretch flex-fill">
          <CPChargePoint :chargepoint="chargepoint" :full-width="true"></CPChargePoint>
        </div>
      </swiper-slide>
    </swiper-container>
  <!-- </div> -->
  <CPSimpleList v-if="globalConfig.simpleCpList"></CPSimpleList>
</template>

<script setup lang="ts">
import { computed, onMounted } from 'vue'
import { chargePoints } from './model'
import { globalConfig, widescreen } from '@/assets/js/themeConfig'
import CPChargePoint from './CPChargePoint.vue'
import CPSimpleList from './cpSimpleList/CPSimpleList.vue'
import type Swiper from 'swiper'
import 'swiper/css'
import 'swiper/css/pagination'

let swiper: Swiper
let swiperEl: any

const chargepointsToDisplay = computed(() => {
  let cpArray = Object.values(chargePoints)
  updateLayout()
  return cpArray
})

const totalWidth = computed(() => {
  switch (Object.values(chargePoints).length) {
    case 0: return (globalConfig.preferWideBoxes) ? "col-lg-6" : "col-lg-4"
    case 1: return (globalConfig.preferWideBoxes) ? "col-lg-6" : "col-lg-4"
    case 2: return (globalConfig.preferWideBoxes) ? "col-lg-12" : "col-lg-8 "
    default: return "col-lg-12"
  }
})
function updateLayout() {
  // update swiper layout
  if (swiper) {
    let slidesPerView = "1"
    if (widescreen.value) {
      switch (Object.values(chargePoints).length) {
        case 0:
        case 1: slidesPerView = "1"
          break
        case 2: slidesPerView = "2"
          break
        default: slidesPerView = "3"
      }
    }
    swiperEl.setAttribute('slides-per-view', slidesPerView);
    swiper.update()

  }
}

onMounted(() => {
  swiperEl = document.querySelector('.swiper-chargepoints')
  if (swiperEl) {
    swiper = (swiperEl as any).swiper
  }
  window.addEventListener('resize', updateLayout)
})

</script>
<style scoped>

</style>
