<template>
  <div :style="color ? { color } : undefined">
    <component :is="iconComponent" v-if="iconComponent" />
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue';

import GridIcon from 'src/components/svgIcons/GridIcon.vue';
import CounterIcon from 'src/components/svgIcons/CounterIcon.vue';
import BatteryIcon from 'src/components/svgIcons/BatteryIcon.vue';
import ChargePointIcon from 'src/components/svgIcons/ChargePointIcon.vue';
import VehicleIcon from 'src/components/svgIcons/VehicleIcon.vue';
import PvIcon from 'src/components/svgIcons/PvIcon.vue';
import HouseIcon from 'src/components/svgIcons/HouseIcon.vue';

const props = defineProps<{
  type: string;
  color?: string | null;
}>();

const iconMap = {
  grid: GridIcon,
  counter: CounterIcon,
  battery: BatteryIcon,
  chargepoint: ChargePointIcon,
  pv: PvIcon,
  house: HouseIcon,
  vehicle: VehicleIcon,
};

const iconComponent = computed(() => {
  // handle secondary IDs like "battery-1"
  const iconName = props.type.split('-')[0];
  return iconMap[iconName] || null;
});
</script>
