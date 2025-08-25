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
import { Screen } from 'quasar';

const props = defineProps<{
  items: number[];
}>();

const slideItemWidth = ref<number | null>(null);
const currentSlideItem = ref<number | null>(null);
const animated = ref<boolean>(true);
const carouselRef = ref<{ $el: HTMLElement } | null>(null);
const itemRef = ref<(HTMLElement | null)[]>([]);

const showArrows = computed(() => {
  return groupedItems.value.length > 1 && Screen.gt.xs;
});

const storeSlideItemWidth = (width: number) => {
  console.log('Storing slide item width:', width);
  slideItemWidth.value = width;
};

const currentSlide = computed({
  get: () => {
    if (currentSlideItem.value == null) {
      return 0; // Always show the first slide if a specific item is not set
    }
    // Find the index of the slide containing the current item
    let currentSlide = groupedItems.value.findIndex((group) =>
      group.includes(currentSlideItem.value),
    );
    if (currentSlide === -1) {
      return 0; // Default to first slide if item not found
    }
    // Ensure the index is within bounds
    return Math.min(currentSlide, groupedItems.value.length - 1);
  },
  set: (value: number) => {
    // Update currentSlideItem to the first item of the new slide
    currentSlideItem.value = groupedItems.value[value][0];
  },
});

const groupSize = computed(() => {
  let itemWidth = 300; // Default width
  console.debug('Calculating group size...', itemRef.value);
  if (slideItemWidth.value == null) {
    if (
      itemRef.value[0]?.clientWidth &&
      itemRef.value[0].clientWidth != slideItemWidth.value
    ) {
      storeSlideItemWidth(itemRef.value[0].clientWidth);
    } else {
      console.warn('Item width is not set, using default:', itemWidth);
    }
  } else {
    itemWidth = slideItemWidth.value;
  }
  console.debug('Item width:', itemWidth);
  let carouselSlideWidth = 0;
  let padding = 0;
  const slideEl = carouselRef.value?.$el.querySelector('.q-carousel__slide');
  if (slideEl) {
    carouselSlideWidth = slideEl.clientWidth ?? 0;
    const style = window.getComputedStyle(slideEl);
    padding =
      parseFloat(style.paddingLeft || '0') +
      parseFloat(style.paddingRight || '0');
  }
  const maxGroupSize = Math.max(
    1,
    Math.floor((carouselSlideWidth - padding) / itemWidth),
  );

  // Special case: Prevent a second group with only one item,
  // if all items would fit side by side without navigation arrows
  if (
    props.items.length > maxGroupSize &&
    props.items.length <= maxGroupSize * 2 &&
    props.items.length - maxGroupSize === 1
  ) {
    // Check if all items would fit side by side
    if (props.items.length * itemWidth <= carouselSlideWidth) {
      return props.items.length;
    }
  }
  return maxGroupSize;
});

const groupedItems = computed(() => {
  return props.items.reduce((resultArray, item, index) => {
    const chunkIndex = Math.floor(
      index / (groupSize.value ? groupSize.value : props.items.length),
    );
    if (!resultArray[chunkIndex]) {
      resultArray[chunkIndex] = [];
    }
    resultArray[chunkIndex].push(item);
    return resultArray;
  }, [] as number[][]);
});

onMounted(async () => {
  await nextTick(() => {
    window.addEventListener('resize', () => {
      // Trigger a re-render by resetting itemRef
      itemRef.value = [...itemRef.value];
    });
  });
});

watch(
  () => props.items,
  () => {
    // Reset itemRef to trigger re-render
    itemRef.value = [...itemRef.value];
  },
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
