<template>
  <div class="my-card">
    <div class="relative-position" style="height: 40px">
      <q-slider
        v-model="currentCharge"
        :min="0"
        :max="100"
        color="green-7"
        track-size="1em"
        thumb-size="0px"
        readonly
        no-focus
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
        track-size="1em"
        :thumb-size="props.readonly ? '0' : '2em'"
        :readonly="props.readonly"
        @touchstart.stop
        @touchmove.stop
        @touchend.stop
        style="position: absolute; width: 100%"
      />
    </div>

    <div class="row justify-between no-wrap">
      <div class="col">
        <div>Ladestand</div>
        <div>{{ currentCharge }}%</div>
        <div>100km</div>
      </div>
      <div class="col text-center">
        <div>Zielzeit</div>
        <div>keine</div>
      </div>
      <div class="col text-right">
        <div>Ladeziel</div>
        <div>{{ targetCharge }}%</div>
        <div>360km</div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref } from 'vue';

defineOptions({
  name: 'SliderQuasar',
});

const props = defineProps({
  readonly: {
    type: Boolean,
    default: false,
  },
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
