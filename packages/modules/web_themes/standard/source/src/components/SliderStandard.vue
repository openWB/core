<template>
  <div>
    <div>
      <div class="text-subtitle2">{{ props.title }}</div>
    </div>
    <div class="row">
      <q-slider
        :model-value="props.value"
        @update:model-value="emitValue"
        :min="props.min"
        :max="props.max"
        color="primary"
        inner-track-color="blue-grey-2"
        track-size="0.5em"
        thumb-size="1.7em"
        @touchstart.stop
        @touchmove.stop
        @touchend.stop
        style="width: 75%"
      />
      <div class="q-ml-md q-mt-xs items-center no-wrap">
        {{ props.value }} {{ props.units }}
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
//import { ref } from 'vue';

defineOptions({
  name: 'SliderQuasar',
});

const props = defineProps({
  title: {
    type: String,
    default: 'title',
  },
  value: {
    type: Number,
    default: 10,
  },
  max: {
    type: Number,
    default: 100,
  },
  min: {
    type: Number,
    default: 0,
  },
  units: {
    type: String,
    default: '',
  },
});

const emit = defineEmits<{
  'update:value': [value: number];
}>();

const emitValue = (newValue: number | null) => {
  if (newValue !== null) {
    emit('update:value', newValue);
  }
};
</script>
