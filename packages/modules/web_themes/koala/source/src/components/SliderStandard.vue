<template>
  <div>
    <div class="text-subtitle2">{{ title }}</div>
    <div class="row items-center justify-between q-ml-sm">
      <q-slider
        v-model="sliderValue"
        :min="props.discreteValues ? 0 : props.min"
        :max="
          props.discreteValues ? props.discreteValues.length - 1 : props.max
        "
        :step="props.step"
        :color="props.color"
        class="col"
        :track-size="props.trackSize"
        :thumb-size="props.thumbSize"
        :thumb-color="props.thumbColor"
        @touchstart.stop
        @touchmove.stop
        @touchend.stop
      />
      <div
        class="q-ml-sm no-wrap"
        :class="['col-2', 'text-right', pendingClass]"
      >
        {{ displayValue }} {{ displayUnit }}
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue';
import { useDelayModel } from '../composables/useDelayModel';

defineOptions({
  name: 'SliderStandard',
});

const props = withDefaults(
  defineProps<{
    title?: string
    modelValue: number
    max: number
    min: number
    step?: number
    unit?: string
    offValueRight?: number
    offValueLeft?: number
    discreteValues?: number[]
    color?: string
    trackSize?: string
    thumbSize?: string
    thumbColor?: string
  }>(),
  {
    title: 'title',
    step: 1,
    unit: '',
    offValueRight: 105,
    offValueLeft: -1,
    discreteValues: undefined,
    color: 'primary',
    trackSize: '0.5em',
    thumbSize: '1.5em',
    thumbColor: 'primary',
  }
)

const emit = defineEmits<{
  'update:model-value': [value: number];
}>();

const { delayedValue, updatePending } = useDelayModel<number>(props, emit);

const sliderValue = computed({
  get: () => {
    if (props.discreteValues) {
      const index = props.discreteValues.indexOf(delayedValue.value);
      return index >= 0 ? index : 0;
    }
    return delayedValue.value;
  },
  set: (newValue: number) => {
    if (props.discreteValues) {
      delayedValue.value = props.discreteValues[newValue];
    } else {
      delayedValue.value = newValue;
    }
  },
});

const currentValue = computed(() => {
  return props.discreteValues && sliderValue.value !== undefined
    ? (props.discreteValues[sliderValue.value] ?? props.discreteValues[0])
    : delayedValue.value;
});

const displayValue = computed(() => {
  if (
    currentValue.value === props.offValueLeft ||
    currentValue.value === props.offValueRight
  ) {
    return 'Aus';
  }
  return currentValue.value;
});

const displayUnit = computed(() => {
  if (
    currentValue.value === props.offValueLeft ||
    currentValue.value === props.offValueRight
  ) {
    return '';
  }
  return props.unit;
});

const pendingClass = computed(() => (updatePending.value ? 'pending' : ''));
</script>
<style scoped lang="scss">
.pending {
  color: var(--q-negative);
}
</style>
