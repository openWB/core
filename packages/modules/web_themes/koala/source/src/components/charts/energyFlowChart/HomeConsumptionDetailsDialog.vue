<template>
  <q-dialog v-model="visible">
    <q-card class="card-width">
      <q-card-section>
        <div class="row no-wrap items-center">
          <InfoIcon class="title-icon q-mr-md" />
          <div class="text-h6 q-pr-sm">{{ title }}</div>
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
        <q-list dense class="q-pt-sm">
          <q-item v-for="item in items" :key="item.key">
            <q-item-section avatar>
              <component
                :is="item.icon"
                class="item-icon"
                :style="{ color: item.color }"
              />
            </q-item-section>
            <q-item-section>
              <div class="row no-wrap items-center">
                <div class="col">{{ item.name }}</div>
                <div class="q-pl-md text-no-wrap">{{ item.power }}</div>
              </div>
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
import { useMqttStore } from 'src/stores/mqtt-store';
import ConsumerIcon from 'src/assets/icons/owbConsumer.svg?component';
import CounterIcon from 'src/assets/icons/owbCounter.svg?component';
import InfoIcon from 'src/assets/icons/owbInformation.svg?component';

defineOptions({ name: 'HomeConsumptionDetailsDialog' });

interface DetailsItem {
  key: string;
  name: string;
  icon: Component;
  color: string;
  power: string;
}

const props = defineProps<{
  modelValue: boolean;
  scope: 'inHome' | 'notInHome';
  title: string;
}>();

const emit = defineEmits<{
  'update:modelValue': [value: boolean];
}>();

const mqttStore = useMqttStore();

const visible = computed({
  get: () => props.modelValue,
  set: (value) => emit('update:modelValue', value),
});

const items = computed((): DetailsItem[] => {
  const { consumerIds, counterIds } =
    props.scope === 'inHome'
      ? mqttStore.inHomeConsumption
      : mqttStore.notInHomeConsumption;
  return [
    ...consumerIds.map((id) => ({
      key: `consumer-${id}`,
      name: mqttStore.consumerName(id) || `Verbraucher ${id}`,
      icon: ConsumerIcon,
      color: mqttStore.consumerColor(id) || 'var(--q-consumer)',
      power: mqttStore.consumerPower(id, 'textValue') as string,
    })),
    ...counterIds.map((id) => ({
      key: `counter-${id}`,
      name: mqttStore.componentName(id) || `Zähler ${id}`,
      icon: CounterIcon,
      color:
        mqttStore.secondaryCounterColor(id) ||
        'var(--q-secondary-counter-stroke)',
      power: mqttStore.counterPower('textValue', id) as string,
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
.title-icon,
.item-icon {
  width: 28px;
  height: 28px;
}
.title-icon {
  flex-shrink: 0;
  color: var(--q-primary);
}
.q-item__section--avatar {
  min-width: 0;
}

.q-list {
  background-color: transparent;
}
</style>
