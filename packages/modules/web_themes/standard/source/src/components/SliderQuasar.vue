<template>
  <div class="q-pa-md my-card">
    <div class="q-mt-md relative-position" style="height: 40px">
      <q-slider
        v-model="currentCharge"
        :min="0"
        :max="100"
        color="green-7"
        track-size="27px"
        thumb-size="0px"
        readonly
        style="position: absolute; width: 100%; z-index: 1"
      />
      <q-slider
        v-model="targetCharge"
        :min="currentCharge"
        :max="100"
        color="light-green-5"
        inner-track-color="blue-grey-2"
        track-size="27px"
        thumb-size="43px"
        style="position: absolute; width: 100%; z-index:"
      />
    </div>
  </div>
</template>

<script setup>
import { ref } from 'vue';

defineOptions({
  name: 'SliderQuaser',
});

const currentCharge = ref(35);
const targetCharge = ref(80);
</script>

<style scoped>
.my-card {
  width: 100%;
  max-width: 300px;
}
</style>
