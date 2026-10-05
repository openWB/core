<template>
  <q-dialog v-model="visible" :backdrop-filter="isSmallScreen ? '' : 'blur(4px)'">
    <q-card class="card-width">
      <q-card-section>
        <div class="row no-wrap">
          <div class="text-h6 q-pr-sm">Im Hausverbrauch enthalten:</div>
          <q-space />
          <q-btn
            icon="close"
            flat
            round
            dense
            v-close-popup
            class="close-btn"
          />
        </div>
      </q-card-section>
      <q-separator />
      <q-card-section class="q-pa-none">
        <q-list>
          <q-item v-for="item in items" :key="item.key">
            <q-item-section avatar>
              <component
                :is="item.icon"
                class="item-icon"
                :style="{ color: item.color }"
              />
            </q-item-section>
            <q-item-section>
              <q-item-label>{{ item.name }}</q-item-label>
            </q-item-section>
          </q-item>
        </q-list>
      </q-card-section>
    </q-card>
  </q-dialog>
</template>

<script setup lang="ts">
import { computed } from 'vue';
import type { Component } from 'vue';
import { Screen } from 'quasar';
import { useMqttStore } from 'src/stores/mqtt-store';
import ConsumerIcon from 'src/assets/icons/owbConsumer.svg?component';
import CounterIcon from 'src/assets/icons/owbCounter.svg?component';

defineOptions({ name: 'HomeConsumptionDetailsDialog' });

interface DetailsItem {
  key: string;
  name: string;
  icon: Component;
  color: string;
}

const props = defineProps<{
  modelValue: boolean;
}>();

const emit = defineEmits<{
  'update:modelValue': [value: boolean];
}>();

const mqttStore = useMqttStore();

const visible = computed({
  get: () => props.modelValue,
  set: (value) => emit('update:modelValue', value),
});
const isSmallScreen = computed(() => Screen.lt.sm);

const items = computed((): DetailsItem[] => {
  const { consumerIds, counterIds } = mqttStore.inHomeConsumption;
  return [
    ...consumerIds.map((id) => ({
      key: `consumer-${id}`,
      name: mqttStore.consumerName(id) || `Verbraucher ${id}`,
      icon: ConsumerIcon,
      color: mqttStore.consumerColor(id) || 'var(--q-consumer)',
    })),
    ...counterIds.map((id) => ({
      key: `counter-${id}`,
      name: mqttStore.componentName(id) || `Zähler ${id}`,
      icon: CounterIcon,
      color:
        mqttStore.secondaryCounterColor(id) ||
        'var(--q-secondary-counter-stroke)',
    })),
  ];
});
</script>

<style lang="scss" scoped>
.card-width {
  width: 400px;
  max-width: 90vw;
}
.close-btn {
  height: 2.5em;
  width: 2.5em;
}
.item-icon {
  width: 28px;
  height: 28px;
}
</style>
