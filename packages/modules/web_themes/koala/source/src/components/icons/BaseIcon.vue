<script setup lang="ts">
import { computed } from 'vue';

import GridIcon from 'src/components/icons/GridIcon.vue';
import CounterIcon from 'src/components/icons/CounterIcon.vue';
import BatteryIcon from 'src/components/icons/BatteryIcon.vue';
import ChargePointIcon from 'src/components/icons/ChargePointIcon.vue';
import VehicleIcon from 'src/components/icons/VehicleIcon.vue';
import PvIcon from 'src/components/icons/PvIcon.vue';
import HouseIcon from 'src/components/icons/HouseIcon.vue';

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
  const baseType = props.type.split('-')[0];
  return iconMap[baseType as keyof typeof iconMap] || null;
});
</script>

<template>
  <div :style="color ? { color } : undefined">
    <component :is="iconComponent" v-if="iconComponent" />
  </div>
</template>
