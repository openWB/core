<template>
  <div>
    <div>
      <div class="text-subtitle2">{{ props.title }}</div>
    </div>
    <div class="row">
      <q-slider
        v-model="value"
        :min="props.min"
        :max="props.max"
        :step="props.step"
        color="primary"
        style="width: 75%"
        inner-track-color="blue-grey-2"
        track-size="0.5em"
        thumb-size="1.7em"
        @touchstart.stop
        @touchmove.stop
        @touchend.stop
        @change="updateValue"
      />
      <div class="q-ml-md q-mt-xs items-center no-wrap" :class="myClass">
        {{ value }} {{ props.unit }}
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed, ref, watch } from 'vue';

defineOptions({
  name: 'SliderStandard',
});

const props = defineProps({
  title: {
    type: String,
    default: 'title',
  },
  modelValue: {
    type: Number,
  },
  max: {
    type: Number,
    required: true,
  },
  min: {
    type: Number,
    required: true,
  },
  step: {
    type: Number,
    default: 1,
  },
  unit: {
    type: String,
    default: '',
  },
});

const emit = defineEmits<{
  'update:model-value': [value: number];
}>();

const tempValue = ref<number | undefined>(props.modelValue);
const updateTimeout = ref<NodeJS.Timeout | null>(null);

const updatePending = computed(() => {
  return tempValue.value !== props.modelValue;
});

const value = computed({
  get: () => tempValue.value,
  set: (newValue: number) => {
    if (updateTimeout.value) {
      clearTimeout(updateTimeout.value);
    }
    tempValue.value = newValue;
  },
});

const updateValue = (newValue: number) => {
  if (updatePending.value) {
    updateTimeout.value = setTimeout(() => {
      emit('update:model-value', newValue);
    }, 2000);
  }
};

watch(
  () => props.modelValue,
  (newValue) => {
    tempValue.value = newValue;
  },
);

const myClass = computed(() => {
  return updatePending.value ? 'pending' : '';
});
</script>

<style lang="scss" scoped>
.pending {
  color: $red;
}
</style>
