<template>
  <div>
    <div class="text-subtitle2">{{ title }}</div>
    <div class="row items-center q-mx-sm">
      <q-range
        v-model="delayedValue"
        :min="props.min"
        :max="props.max"
        :step="props.step"
        :markers="props.markers"
        :left-label-color="minChanged ? 'negative' : 'primary'"
        :right-label-color="maxChanged ? 'negative' : 'primary'"
        label
        label-always
        switch-label-side
        color="primary"
        class="col q-pb-xl"
        track-size="0.5em"
        thumb-size="1.7em"
        @touchstart.stop
        @touchmove.stop
        @touchend.stop
      />
    </div>
  </div>
</template>
<script setup lang="ts">
import { computed } from 'vue';
import { useDelayModel } from '../composables/useDelayModel';
import { RangeValue } from '../stores/mqtt-store-model';

const props = withDefaults(
  defineProps<{
    title?: string
    modelValue: RangeValue
    min: number
    max: number
    step?: number
    markers?: boolean | number
  }>(),
  {
    title: '',
    step: 1,
    markers: false,
  }
)

const emit = defineEmits<{
  'update:model-value': [value: RangeValue];
}>();

const { delayedValue } = useDelayModel<RangeValue>(props, emit);

const minChanged = computed(() =>
  delayedValue.value.min !== props.modelValue.min
)

const maxChanged = computed(() =>
  delayedValue.value.max !== props.modelValue.max
)
</script>
