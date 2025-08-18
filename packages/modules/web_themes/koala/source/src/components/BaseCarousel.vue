<template>
  <q-carousel
    ref="carouselRef"
    v-model="currentSlide"
    swipeable
    :animated="animated"
    control-color="primary"
    infinite
    @update:model-value="handleSlideChange"
    padding
    :navigation="groupedItems.length > 1"
    :arrows="groupedItems.length > 1 && $q.screen.gt.xs"
    class="carousel-height"
    transition-next="slide-left"
    transition-prev="slide-right"
    @mousedown.prevent
  >
    <q-carousel-slide
      v-for="(group, index) in groupedItems"
      :key="index"
      :name="index"
      class="row no-wrap justify-center carousel-slide"
    >
      <div
        v-for="(item, idx) in group"
        :key="item"
        class="item-container"
        :ref="idx === 0 && index === 0 ? 'itemRef' : undefined"
      >
        <slot name="item" :item="item"></slot>
      </div>
    </q-carousel-slide>
  </q-carousel>
</template>

<script setup lang="ts">
import { ref, computed, watch, nextTick, onMounted } from 'vue';
import { useQuasar } from 'quasar';

const props = defineProps<{
  items: number[];
}>();

const $q = useQuasar();
const currentSlide = ref<number>(0);
const animated = ref<boolean>(true);
const carouselRef = ref<{ $el: HTMLElement } | null>(null);
const itemRef = ref<(HTMLElement | null)[]>([]);
const groupSize = ref<number>(2);

const updateGroupSize = () => {
  if (!itemRef.value[0]) {
    groupSize.value = 1; // Fallback to 1 if no items are available
    setTimeout(updateGroupSize, 50);
    return;
  }
  const carouselSlideWidth =
    carouselRef.value?.$el.querySelector('.q-carousel__slide')?.clientWidth ??
    0;
  const itemWidth = itemRef.value[0]?.clientWidth ?? 300; // Fallback
  // Get computed padding from the carousel slide element
  let padding = 0;
  const slideEl = carouselRef.value?.$el.querySelector('.q-carousel__slide');
  if (slideEl) {
    const style = window.getComputedStyle(slideEl);
    padding =
      parseFloat(style.paddingLeft || '0') +
      parseFloat(style.paddingRight || '0');
  }
  groupSize.value = Math.max(
    1,
    Math.floor((carouselSlideWidth - padding) / itemWidth),
  );
};

const groupedItems = computed(() => {
  return props.items.reduce((resultArray, item, index) => {
    const chunkIndex = Math.floor(index / groupSize.value);
    if (!resultArray[chunkIndex]) {
      resultArray[chunkIndex] = [];
    }
    resultArray[chunkIndex].push(item);
    return resultArray;
  }, [] as number[][]);
});

onMounted(async () => {
  await nextTick(() => {
    updateGroupSize();
    window.addEventListener('resize', updateGroupSize);
  });
});

watch(
  () => props.items,
  () => updateGroupSize(),
);

const handleSlideChange = () => {
  const currentScroll = window.scrollY;
  nextTick(() => {
    window.scrollTo(0, currentScroll);
  });
};
</script>

<style scoped>
.carousel-slide {
  padding: 0;
}

.item-container {
  padding: 0.25em;
}

.carousel-height {
  min-height: fit-content;
  height: 100%;
}
</style>
