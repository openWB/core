<template>
  <div class="row py-0 px-0 m-0">
    <swiper-container :space-between="0" :pagination="{ clickable: true }" slides-per-view="1"
      class="p-0 m-0 swiper-carousel" :breakpoints="{
        992: { slidesPerView: 3, spaceBetween: 0 }
      }">

      <swiper-slide>
        <div :class="(widescreen) ? 'mb-0' : 'mb-5'" class="flex-fill d-flex align-items-stretch">
          <slot name="item1"></slot>
        </div>
      </swiper-slide>
      <swiper-slide>
        <div :class="(widescreen) ? 'mb-0' : 'mb-5'" class="flex-fill d-flex align-items-stretch">
          <slot name="item2"></slot>
        </div>
      </swiper-slide>
      <swiper-slide>
        <div :class="(widescreen) ? 'mb-0' : 'mb-5'" class="flex-fill d-flex align-items-stretch">
          <slot name="item3"></slot>
        </div>
      </swiper-slide>
    </swiper-container>
    <!--  <swiper-pagination></swiper-pagination> -->

  </div>
</template>

<script setup lang="ts">
import 'swiper/css'
import 'swiper/css/pagination'
import { widescreen } from '@/assets/js/themeConfig';


</script>
<style scoped>
.button {
  color: var(--color-fg);
}
</style>
