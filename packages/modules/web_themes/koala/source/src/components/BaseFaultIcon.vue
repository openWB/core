<template>
  <span class="fault-icon">
    <q-icon
      v-if="props.faultState > 0"
      :name="iconName"
      :size="iconSize"
      :color="iconColor"
    />
  </span>
</template>

<script setup lang="ts">
import { computed } from 'vue';
import { Screen } from 'quasar';

const props = defineProps<{
  faultState: number;
}>();

const iconSize = computed(() => (Screen.lt.md ? '18px' : '22px'));

const iconName = computed(() => (props.faultState === 2 ? 'error' : 'warning'));

const iconColor = computed(() =>
  props.faultState === 2 ? 'negative' : 'warning',
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
