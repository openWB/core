<template>
	<swiper-container
		v-if="!props.compact"
		:space-between="0"
		:slides-per-view="1"
		:pagination="{ clickable: true }"
		class="cplist m-0 p-0 d-flex align-items-stretch"
		:class="cplistclasses"
	>
		<swiper-slide
			v-for="chargepoint in chargepointsToDisplay"
			:key="chargepoint.id"
		>
			<div
				:class="widescreen ? 'mb-0' : 'mb-5'"
				class="d-flex align-items-stretch flex-fill"
			>
				<CPChargePoint :chargepoint="chargepoint" :full-width="true" />
			</div>
		</swiper-slide>
	</swiper-container>
	<CpSimpleList2 v-if="props.compact" />
</template>

<script setup lang="ts">
import { computed, onMounted } from 'vue'
import { chargePoints } from './model'
import { globalConfig, widescreen } from '@/assets/js/themeConfig'
import CPChargePoint from './CPChargePoint.vue'
import Swiper from 'swiper'
import 'swiper/css'
import 'swiper/css/pagination'
import type { SwiperContainer } from 'swiper/element'
import CpSimpleList2 from './cpSimpleList/CpSimpleList2.vue'

let swiper: Swiper
let swiperEl: SwiperContainer
//props
const props = defineProps<{
	id: string
	compact: boolean
}>()

const chargepointsToDisplay = computed(() => {
	let cpArray = Object.values(chargePoints)
	updateLayout()
	return cpArray
})
const cplistclasses = computed(() => {
	return totalWidth.value + ' ' + widgetId.value
})
const totalWidth = computed(() => {
	switch (Object.values(chargePoints).length) {
		case 0:
			return globalConfig.preferWideBoxes ? 'col-lg-6' : 'col-lg-4'
		case 1:
			return globalConfig.preferWideBoxes ? 'col-lg-6' : 'col-lg-4'
		case 2:
			return globalConfig.preferWideBoxes ? 'col-lg-12' : 'col-lg-8 '
		default:
			return 'col-lg-12'
	}
})
const widgetId = computed(() => {
	return 'swiper-chargepoints-' + props.id
})
function updateLayout() {
	// update swiper layout
	let tmp = document.querySelector('.' + widgetId.value)
	if (tmp) {
		swiperEl = tmp as SwiperContainer
		swiper = swiperEl.swiper
	}
	if (swiper) {
		let slidesPerView = '1'
		if (widescreen.value) {
			switch (Object.values(chargePoints).length) {
				case 0:
				case 1:
					slidesPerView = '1'
					break
				case 2:
					slidesPerView = '2'
					break
				default:
					slidesPerView = '3'
			}
		}
		swiperEl.setAttribute('slides-per-view', slidesPerView)
		swiper.update()
	}
}

onMounted(() => {
	let tmp = document.querySelector('.' + widgetId.value)
	if (tmp) {
		swiperEl = tmp as SwiperContainer
		swiper = swiperEl.swiper
	}
	window.addEventListener('resize', updateLayout)
	window.document.addEventListener('visibilitychange', updateLayout)
})
</script>
<style scoped></style>
