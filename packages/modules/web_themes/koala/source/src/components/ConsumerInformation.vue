<template>
  <div class="consumer-grid-wrapper">
    <div class="consumer-grid">
      <ConsumerCard
        v-for="item in consumerIds"
        :key="item"
        :consumer-id="item"
        full-height
      />
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue';
import { useMqttStore } from 'src/stores/mqtt-store';

import ConsumerCard from 'src/components/ConsumerCard.vue';

const mqttStore = useMqttStore();

const consumerIds = computed(() => mqttStore.consumerIds);
</script>

<style scoped lang="scss">
.consumer-grid-wrapper {
  flex: 1 1 auto;
  min-height: 0;
  width: 100%;
  overflow-y: auto;
}

.consumer-grid {
  display: grid;
  gap: 0.5em;
  grid-template-columns: repeat(
    auto-fit,
    minmax(min(22em, calc(50% - 0.5em)), 22em)
  );
  justify-content: center;
  align-content: start;
  padding: 0.5em;
}
</style>
