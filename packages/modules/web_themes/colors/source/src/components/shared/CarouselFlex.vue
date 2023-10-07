<template>
	<swiper :space-between="30" :slides-per-view="1" :pagination="{ clickable: true }" :modules="modules" @swiper="onSwiper"
		@slideChange="onSlideChange" class="carousel2">
		<slot></slot>
		<swiper-slide>foo</swiper-slide>
		<swiper-slide>bar</swiper-slide>
	</swiper>
</template>
<script setup lang="ts">
import { Swiper, SwiperSlide } from "swiper/vue"
import { useSwiper } from "swiper/vue"
import { Pagination } from 'swiper/modules'
import "swiper/css"
import "swiper/css/pagination"

//const swiper = useSwiper()
const onSwiper = (e: any) => {
	// const [swiper, progress] = e.detail;
	console.log(e)
};
const onSlideChange = (e: any) => {
	console.log('slide changed')
}
const modules = [Pagination]

</script>
<style scoped></style>