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
    class="carousel-height q-mt-md"
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
        :style="`min-height: ${maxCardHeight}px`"
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
  watch,
  nextTick,
  onMounted,
  onBeforeUnmount,
  provide,
} from 'vue';
import { useQuasar } from 'quasar';

const props = defineProps<{
  items: number[];
}>();

const $q = useQuasar();
const currentSlide = ref<number>(0);
const animated = ref<boolean>(true);
const carouselRef = ref<{ $el: HTMLElement } | null>(null);
const carouselWidth = ref(0);
let resizeObserver: ResizeObserver | null = null;
const maxCardHeight = ref<number>(0);

// Calculates and sets the maximum card height for all cards in the active slide
const updateMaxCardHeight = () => {
  // Quasar adds CSS class .q-carousel__slide--active when the slide is active - calculation then made only on active slide/s
  const cards = document.querySelectorAll(
    '.q-carousel__slide--active .item-container',
  );
  const heights = Array.from(cards).map(
    (card) => (card as HTMLElement).offsetHeight,
  );
  maxCardHeight.value = Math.max(...heights);
};

// Sets up a MutationObserver to watch for changes in the cards of the active slide
const observeCardChanges = () => {
  const observer = new MutationObserver(() => {
    updateMaxCardHeight();
  });
  const cards = document.querySelectorAll(
    '.q-carousel__slide--active .item-container',
  );
  cards.forEach((card) => {
    observer.observe(card, {
      childList: true,
      subtree: true,
      attributes: true,
    });
  });
};

onMounted(() => {
  nextTick(() => {
    if (carouselRef.value && carouselRef.value.$el) {
      carouselWidth.value = carouselRef.value.$el.offsetWidth;
      // Set up ResizeObserver to update width and card height on resize
      resizeObserver = new ResizeObserver(() => {
        if (carouselRef.value && carouselRef.value.$el) {
          carouselWidth.value = carouselRef.value.$el.offsetWidth;
          updateMaxCardHeight();
        }
      });
      resizeObserver.observe(carouselRef.value.$el);
    }
    // Calculate initial card height and set up MutationObserver
    updateMaxCardHeight();
    observeCardChanges();
  });
});

onBeforeUnmount(() => {
  if (resizeObserver && carouselRef.value && carouselRef.value.$el) {
    resizeObserver.unobserve(carouselRef.value.$el);
  }
});

const effectiveCardWidth = ref<number | undefined>(undefined);

// Function provided to child components
const setCardWidth = (width: number | undefined) => {
  effectiveCardWidth.value = width ? width + 72 : undefined; // Add 72px to account for padding / margins / navigation buttons in carousel
};

provide('setCardWidth', setCardWidth);

// Computes how many cards can fit in the carousel based on carousel width and the card width
const groupSize = computed(() => {
  return effectiveCardWidth.value
    ? Math.max(1, Math.floor(carouselWidth.value / effectiveCardWidth.value))
    : 380;
});

// Groups the items into arrays for each slide, based on the computed group size
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

// Updates the current slide and recalculates card heights when the grouped items change
watch(
  () => groupedItems.value,
  async (newValue, oldValue) => {
    const findSlide = (itemId: number) => {
      return newValue.findIndex((group) => group.includes(itemId));
    };
    if (!oldValue || oldValue.length === 0) {
      currentSlide.value = 0;
      return;
    }
    animated.value = false;
    currentSlide.value = Math.max(
      findSlide(oldValue[currentSlide.value][0]),
      0,
    );
    await nextTick();
    animated.value = true;
    updateMaxCardHeight();
    observeCardChanges();
  },
);

// Called when the slide changes; recalculates card heights and scrolls to the previous position
const handleSlideChange = () => {
  const currentScroll = window.scrollY;
  nextTick(() => {
    updateMaxCardHeight();
    observeCardChanges();
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
