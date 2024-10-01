<template>
  <div class="my-card">
    <div class="relative-position" style="height: 40px">
      <q-slider
        v-model="currentCharge"
        :min="0"
        :max="100"
        color="green-7"
        track-size="20px"
        thumb-size="0px"
        readonly
        @touchstart.stop
        @touchmove.stop
        @touchend.stop
        style="position: absolute; width: 100%; z-index: 1"
      />
      <q-slider
        v-model="targetCharge"
        :min="currentCharge"
        :max="100"
        color="light-green-5"
        inner-track-color="blue-grey-2"
        track-size="20px"
        thumb-size="37px"
        @touchstart.stop
        @touchmove.stop
        @touchend.stop
        style="position: absolute; width: 100%; z-index:"
      />
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref } from 'vue';

defineOptions({
  name: 'SliderQuasar',
});

const currentCharge = ref<number>(35);
const targetCharge = ref<number>(80);
</script>

<style scoped>
.my-card {
  width: 100%;
  max-width: 300px;
}
</style>