<template>
  <div>
    <div>
      <div class="text-subtitle2">{{ props.title }}</div>
    </div>
    <div class="row">
      <q-slider
        v-model="value"
        :min="props.discreteValues ? 0 : props.min"
        :max="
          props.discreteValues ? props.discreteValues.length - 1 : props.max
        "
        :step="props.step"
        color="primary"
        style="width: 75%"
        track-size="0.5em"
        thumb-size="1.7em"
        @touchstart.stop
        @touchmove.stop
        @touchend.stop
        @change="updateValue"
      />
      <div class="q-ml-md q-mt-xs items-center no-wrap" :class="myClass">
        {{ displayValue }} {{ displayUnit }}
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed, ref, watch, onBeforeUnmount } from 'vue';

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
  offValueRight: {
    type: Number,
    default: 105,
  },
  offValueLeft: {
    type: Number,
    default: -1,
  },
  discreteValues: {
    type: Array as () => number[],
    default: undefined,
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
  get: () => {
    if (props.discreteValues) {
      const index = props.discreteValues.indexOf(
        tempValue.value ?? props.discreteValues[0],
      );
      return index >= 0 ? index : 0;
    }
    return tempValue.value;
  },
  set: (newValue: number) => {
    if (updateTimeout.value) {
      clearTimeout(updateTimeout.value);
    }
    if (props.discreteValues) {
      tempValue.value = props.discreteValues[newValue];
    } else {
      tempValue.value = newValue;
    }
  },
});

const updateValue = (newValue: number) => {
  if (updatePending.value) {
    if (updateTimeout.value) {
      clearTimeout(updateTimeout.value);
    }
    updateTimeout.value = setTimeout(() => {
      emit(
        'update:model-value',
        props.discreteValues ? props.discreteValues[newValue] : newValue,
      );
    }, 2000);
  }
};

const displayValue = computed(() => {
  const currentValue =
    props.discreteValues && value.value !== undefined
      ? props.discreteValues[value.value]
      : value.value;

  if (
    currentValue === props.offValueLeft ||
    currentValue === props.offValueRight
  ) {
    return 'Aus';
  }
  return currentValue;
});

const displayUnit = computed(() => {
  const currentValue =
    props.discreteValues && value.value !== undefined
      ? props.discreteValues[value.value]
      : value.value;

  if (
    currentValue === props.offValueLeft ||
    currentValue === props.offValueRight
  ) {
    return '';
  }
  return props.unit;
});

watch(
  () => props.modelValue,
  (newValue) => {
    tempValue.value = newValue;
  },
);

onBeforeUnmount(() => {
  if (updateTimeout.value) {
    clearTimeout(updateTimeout.value);
    const currentValue = value.value !== undefined ? value.value : 0;
    emit(
      'update:model-value',
      props.discreteValues ? props.discreteValues[currentValue] : currentValue,
    );
  }
});

const myClass = computed(() => {
  return updatePending.value ? 'pending' : '';
});
</script>

<style lang="scss" scoped>
.pending {
  color: $red;
}
</style>
