<template>
  <q-carousel
    v-model="currentSlide"
    swipeable
    :animated="animated"
    control-color="primary"
    infinite
    padding
    :navigation="groupedItems.length > 1"
    :arrows="groupedItems && $q.screen.gt.xs"
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
      <div v-for="item in group" :key="item" class="item-container">
        <slot name="item" :item="item"></slot>
      </div>
    </q-carousel-slide>
  </q-carousel>
</template>

<script setup lang="ts">
import { ref, computed, watch, nextTick } from 'vue';
import { useQuasar } from 'quasar';

const props = defineProps<{
  items: number[];
}>();

const $q = useQuasar();
const currentSlide = ref<number>(0);
const animated = ref<boolean>(true);

/**
 * Group the items in chunks of 2 for large screens and 1 for small screens.
 */
const groupedItems = computed(() => {
  const groupSize = $q.screen.width > 800 ? 2 : 1;
  return props.items.reduce((resultArray, item, index) => {
    const chunkIndex = Math.floor(index / groupSize);
    if (!resultArray[chunkIndex]) {
      resultArray[chunkIndex] = [];
    }
    resultArray[chunkIndex].push(item);
    return resultArray;
  }, [] as number[][]);
});

/**
 * Update the current slide when the grouped items change.
 * This may happen when the items are sorted or filtered or when the screen size changes.
 * We try to keep the same item in view when the slide changes.
 */
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
    // Prevent animation when the current slide is modified
    animated.value = false;
    currentSlide.value = Math.max(
      findSlide(oldValue[currentSlide.value][0]),
      0,
    );
    await nextTick();
    animated.value = true;
  },
);
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
}
</style>
