<template>
	<swiper
		:space-between="30"
		:slides-per-view="1"
		:pagination="{ clickable: true }"
		:modules="modules"
		class="carousel2"
	>
		<slot />
		<swiper-slide>foo</swiper-slide>
		<swiper-slide>bar</swiper-slide>
	</swiper>
</template>
<script setup lang="ts">
import { Swiper, SwiperSlide } from 'swiper/vue'
import { Pagination } from 'swiper/modules'
import 'swiper/css'
import 'swiper/css/pagination'

const modules = [Pagination]
</script>
<style scoped></style>
