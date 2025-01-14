<template>
	<div class="row py-0 px-0 m-0">
		<swiper-container
			:space-between="0"
			:pagination="{ clickable: true }"
			slides-per-view="1"
			class="p-0 m-0 swiper-carousel"
			:breakpoints="bpoints"
		>
			<swiper-slide>
				<div
					:class="widescreen ? 'mb-0' : 'mb-5'"
					class="flex-fill d-flex align-items-stretch"
				>
					<slot name="item1" />
				</div>
			</swiper-slide>
			<swiper-slide>
				<div
					:class="widescreen ? 'mb-0' : 'mb-5'"
					class="flex-fill d-flex align-items-stretch"
				>
					<slot name="item2" />
				</div>
			</swiper-slide>
			<swiper-slide>
				<div
					:class="widescreen ? 'mb-0' : 'mb-5'"
					class="flex-fill d-flex align-items-stretch"
				>
					<slot name="item3" />
				</div>
			</swiper-slide>
		</swiper-container>
	</div>
</template>

<script setup lang="ts">
import 'swiper/css'
import 'swiper/css/pagination'
import { globalConfig, widescreen } from '@/assets/js/themeConfig'
import { computed, onMounted, ref, watch } from 'vue'
import type Swiper from 'swiper'
import 'swiper/css'
import 'swiper/css/pagination'
import type { SwiperContainer } from 'swiper/element'

let swiper: Swiper
let swiperEl: SwiperContainer
const zoom = ref(false)
const bpoints = computed(() => {
	if (zoom.value) {
		return { 992: { slidesPerView: 1, spaceBetween: 0 } }
	} else {
		return { 992: { slidesPerView: 3, spaceBetween: 0 } }
	}
})
// Zoom into powergraph if user clicked the zoom button (and reverse)
watch(
	() => globalConfig.zoomGraph,
	(zoomGraph) => {
		// update swiper layout
		if (swiper) {
			let slidesPerView = zoomGraph ? '1' : '3'
			swiperEl.setAttribute('slides-per-view', slidesPerView)
			swiper.activeIndex = globalConfig.zoomedWidget
			swiper.update()
		}
	},
)
onMounted(() => {
	let tmp = document.querySelector('.swiper-carousel')
	if (tmp) {
		swiperEl = tmp as SwiperContainer
		swiper = swiperEl.swiper
	}
})
</script>
<style scoped>
.button {
	color: var(--color-fg);
}
</style>
