<template>
	<swiper-slide>
		<slot />
	</swiper-slide>
</template>

<script setup lang="ts">
import { SwiperSlide } from 'swiper/vue'
import 'swiper/css'
import 'swiper/css/pagination'
</script>
<style scoped>
.swiper-slide {
	width: 100%;
}
</style>
