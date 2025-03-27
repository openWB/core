<template>
  <div class="my-card">
    <div class="slider-container">
      <!-- For SoC mode -->
      <div v-if="props.limitMode !== 'amount'">
        <q-slider
          v-model="currentValue"
          :min="0"
          :max="100"
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
          v-model="targetValue"
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

      <!-- For Energy Amount mode -->
      <div v-else>
        <q-slider
          v-model="currentValue"
          :min="0"
          :max="targetValue"
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
      </div>
    </div>

    <div class="row justify-between no-wrap">
      <div class="col">
        <div>{{ props.limitMode !== 'amount' ? 'Ladestand' : 'Geladen' }}</div>
        <div>
          {{
            props.limitMode !== 'amount'
              ? currentValue + '%'
              : formatEnergy(currentValue)
          }}
        </div>
      </div>
      <div
        v-if="props.chargeMode === 'scheduled_charging'"
        class="col text-center"
      >
        <div>Zielzeit</div>
        <div>{{ props.targetTime }}</div>
      </div>
      <div class="col text-right">
        <div>
          {{ props.limitMode !== 'amount' ? 'Ladeziel' : 'Energieziel' }}
        </div>
        <div>
          {{
            props.limitMode !== 'amount'
              ? targetValue + '%'
              : formatEnergy(targetValue)
          }}
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue';

defineOptions({
  name: 'SliderQuasar',
});

const props = defineProps({
  readonly: {
    type: Boolean,
    default: false,
  },
  chargeMode: {
    type: String,
    default: '',
  },
  connectedVehicleSoc: {
    type: Number,
    default: 0,
  },
  targetSoc: {
    type: Number,
    default: 0,
  },
  targetTime: {
    type: String,
    default: 'keine',
  },
  limitMode: {
    type: String,
    default: 'soc',
  },
  currentEnergyCharged: {
    type: Number,
    default: 0,
  },
  targetEnergyAmount: {
    type: Number,
    default: 0,
  },
});

// Unified current and target values that adapt based on the limitMode
const currentValue = computed(() =>
  props.limitMode === 'amount'
    ? props.currentEnergyCharged
    : props.connectedVehicleSoc,
);

const targetValue = computed(() =>
  props.limitMode === 'amount' ? props.targetEnergyAmount : props.targetSoc,
);

const formatEnergy = (value: number) => {
  if (value >= 1000) {
    return (value / 1000).toFixed(2) + ' kWh';
  } else {
    return value.toFixed(0) + ' Wh';
  }
};
</script>

<style scoped>
.my-card {
  width: 100%;
  max-width: 300px;
}

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
