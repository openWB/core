<template>
  <q-carousel
    ref="carouselRef"
    v-model="currentSlide"
    swipeable
    :animated="true"
    control-color="primary"
    infinite
    @update:model-value="handleSlideChange"
    padding
    :navigation="groupedItems.length > 1"
    :arrows="showArrows"
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
        v-for="item in group"
        :key="item"
        class="item-container"
        ref="itemRef"
      >
        <slot name="item" :item="item"></slot>
      </div>
    </q-carousel-slide>
  </q-carousel>
</template>

<script setup lang="ts">
import {
  ref,
  computed,
  nextTick,
  onMounted,
  onBeforeUnmount,
  watch,
} from 'vue';
import { Screen } from 'quasar';

const props = defineProps<{ items: number[] }>();

const carouselRef = ref<{ $el: HTMLElement } | null>(null);
const itemRef = ref<HTMLElement | null>(null);
const currentSlide = ref(0);

const itemWidth = ref(100);
const carouselWidth = ref(0);
const carouselPadding = ref(0);
const showArrows = ref(false);

function measure() {
  nextTick(() => {
    if (itemRef.value) {
      itemWidth.value = itemRef.value[0].clientWidth || 300;
    }
    showArrows.value = Screen.gt.xs && groupedItems.value.length > 1;
    if (carouselRef.value?.$el) {
      carouselWidth.value = carouselRef.value.$el.clientWidth || 0;
      const slideEl = carouselRef.value.$el.querySelector('.q-carousel__slide');
      if (slideEl) {
        const style = window.getComputedStyle(slideEl);
        carouselPadding.value =
          parseFloat(style.paddingLeft || '0') +
          parseFloat(style.paddingRight || '0');
      } else {
        console.warn('Could not find .q-carousel__slide element');
      }
    }
  });
}

onMounted(() => {
  measure();
  window.addEventListener('resize', measure, {passive: true});
});

onBeforeUnmount(() => {
  window.removeEventListener('resize', measure);
});

watch(() => props.items, measure);

const groupSize = computed(() => {
  if (!itemWidth.value || !carouselWidth.value) return 1;
  const maxGroup = Math.max(
    1,
    Math.floor(
      (carouselWidth.value - 2 - (showArrows.value ? carouselPadding.value : 50)) /
        itemWidth.value,
    ),
  );
  // Spezialfall: Alle passen nebeneinander
  if (
    props.items.length > maxGroup &&
    props.items.length <= maxGroup + 1 &&
    props.items.length - maxGroup === 1
  ) {
    if (props.items.length * itemWidth.value < carouselWidth.value) {
      return props.items.length;
    }
  }
  return maxGroup;
});

const groupedItems = computed(() => {
  const size = groupSize.value;
  const result: number[][] = [];
  for (let i = 0; i < props.items.length; i += size) {
    result.push(props.items.slice(i, i + size));
  }
  return result;
});

function handleSlideChange(val: number) {
  currentSlide.value = val;
}

watch(groupedItems, (groups) => {
  if (currentSlide.value > groups.length - 1) {
    currentSlide.value = Math.max(0, groups.length - 1);
  }
  measure();
});
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
