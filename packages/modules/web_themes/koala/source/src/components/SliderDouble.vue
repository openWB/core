<template>
  <div class="double-slider-container">
    <div class="slider-container">
      <q-slider
        :model-value="currentValue"
        :min="0"
        :max="maxValue"
        :markers="props.limitMode == 'amount' ? 10000 : 10"
        color="green-7"
        class="current-slider"
        track-size="1.5em"
        thumb-size="0px"
        readonly
        no-focus
        @touchstart.stop
        @touchmove.stop
        @touchend.stop
      />
      <q-slider
        v-if="props.limitMode == 'soc'"
        v-model="target"
        :min="0"
        :max="100"
        color="light-green-5"
        inner-track-color="blue-grey-2"
        class="target-slider"
        track-size="1.5em"
        :thumb-size="props.readonly ? '0' : '2em'"
        :readonly="props.readonly"
        @touchstart.stop
        @touchmove.stop
        @touchend.stop
      />
    </div>
    <div class="row justify-between no-wrap">
      <div class="col">
        <div>{{ props.limitMode == 'amount' ? 'Geladen' : 'Ladestand' }}</div>
        <div>
          {{
            props.limitMode == 'amount'
              ? formatEnergy(currentValue)
              : currentValue + '%'
          }}
          <slot name="update-soc-icon"></slot>
        </div>
      </div>
      <div v-if="props.targetTime" class="col text-center">
        <div>Zielzeit</div>
        <div>{{ props.targetTime }}</div>
      </div>
      <div v-if="targetSet" class="col text-right">
        <div>
          {{ props.limitMode == 'soc' ? 'Ladeziel' : 'Energieziel' }}
        </div>
        <div>
          {{ props.limitMode == 'soc' ? target + '%' : target / 1000 + ' kWh' }}
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue';

defineOptions({
  name: 'SliderDouble',
});

const emit = defineEmits(['update:modelValue']);

const props = defineProps({
  modelValue: {
    type: Number,
    required: false,
    default: -1,
  },
  readonly: {
    type: Boolean,
    default: false,
  },
  chargeMode: {
    type: String,
    default: '',
  },
  limitMode: {
    type: String,
    default: 'soc',
  },
  currentValue: {
    type: Number,
    default: 0,
  },
  targetTime: {
    type: String,
    required: false,
    default: undefined,
  },
});

const target = computed({
  get: () => props.modelValue,
  set: (value) => {
    if (!props.readonly) {
      emit('update:modelValue', value);
    }
  },
});

const targetSet = computed(() => {
  return target.value >= 0 && props.limitMode !== 'none';
});

const maxValue = computed(() => {
  if (['soc', 'none'].includes(props.limitMode)) {
    return 100;
  }
  return target.value;
});

const formatEnergy = (value: number) => {
  if (value >= 1000) {
    return (value / 1000).toFixed(2) + ' kWh';
  } else {
    return value.toFixed(0) + ' Wh';
  }
};
</script>

<style scoped>
.slider-container {
  position: relative;
  height: 40px;
}

.current-slider {
  position: absolute;
  width: 100%;
  z-index: 1;
}

.target-slider {
  position: absolute;
  width: 100%;
}
</style>
