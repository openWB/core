<template>
  <span class="fault-icon">
    <q-icon
      v-if="faultState > 0"
      :name="iconName"
      :size="iconSize"
      :color="iconColor"
    />
  </span>
</template>

<script setup lang="ts">
import { computed } from 'vue';
import { Screen } from 'quasar';
import { useMqttStore } from 'src/stores/mqtt-store';

const props = defineProps<{
  chargePointId: number;
}>();

const mqttStore = useMqttStore();

const iconSize = computed(() => (Screen.lt.md ? '18px' : '22px'));

const faultState = computed(() =>
  mqttStore.chargePointFaultState(props.chargePointId),
);

const iconName = computed(() => (faultState.value === 2 ? 'error' : 'warning'));

const iconColor = computed(() =>
  faultState.value === 2 ? 'negative' : 'warning',
);
</script>

<style scoped lang="scss">
.fault-icon {
  display: inline-flex;
  flex: 0 0 auto;
  align-items: center;
  justify-content: center;
  width: v-bind(iconSize);
}
</style>
