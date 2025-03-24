<template>
  <div class="my-card">
    <div class="relative-position" style="height: 40px">
      <!-- For SoC mode -->
      <div v-if="displayMode === 'soc'">
        <q-slider
          v-model="currentCharge"
          :min="0"
          :max="100"
          color="green-7"
          track-size="1.5em"
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
          :min="0"
          :max="100"
          color="light-green-5"
          inner-track-color="blue-grey-2"
          track-size="1.5em"
          :thumb-size="props.readonly ? '0' : '2em'"
          :readonly="props.readonly"
          @touchstart.stop
          @touchmove.stop
          @touchend.stop
          style="position: absolute; width: 100%"
        />
      </div>

      <!-- For Energy Amount mode -->
      <div v-else-if="displayMode === 'energy'">
        <q-slider
          v-model="currentEnergy"
          :min="0"
          :max="targetEnergy"
          color="green-7"
          track-size="1.5em"
          thumb-size="0px"
          readonly
          no-focus
          @touchstart.stop
          @touchmove.stop
          @touchend.stop
          style="position: absolute; width: 100%; z-index: 1"
        />
      </div>
    </div>

    <div class="row justify-between no-wrap">
      <div class="col">
        <div>{{ displayMode === 'soc' ? 'Ladestand' : 'Geladen' }}</div>
        <div>
          {{
            displayMode === 'soc'
              ? currentCharge + '%'
              : formatEnergy(currentEnergy)
          }}
        </div>
      </div>
      <div v-if="showTargetTime" class="col text-center">
        <div>Zielzeit</div>
        <div>{{ targetTime }}</div>
      </div>
      <div class="col text-right">
        <div>{{ displayMode === 'soc' ? 'Ladeziel' : 'Energieziel' }}</div>
        <div>
          {{
            displayMode === 'soc'
              ? targetCharge + '%'
              : formatEnergy(targetEnergy)
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

const showTargetTime = computed(
  () => props.chargeMode === 'scheduled_charging',
);

const displayMode = computed(() => {
  return props.limitMode === 'amount' ? 'energy' : 'soc';
});

const currentCharge = computed(() => props.connectedVehicleSoc);
const targetCharge = computed(() => props.targetSoc);

const currentEnergy = computed(() => props.currentEnergyCharged);
const targetEnergy = computed(() => props.targetEnergyAmount);

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
</style>
