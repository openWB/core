<template>
  <q-card
    class="card-width"
    :class="{ 'full-height': props.fullHeight }"
  >
    <q-card-section class="row no-wrap items-center justify-between">
      <div class="row no-wrap items-center ellipsis">
        <q-icon
          name="circle"
          :color="statusColor"
          size="12px"
          class="q-mr-sm"
          :title="statusText"
        />
        <div class="text-h6 text-bold ellipsis" :title="name">
          {{ name }}
        </div>
      </div>
      <q-space />
      <q-btn
        icon="settings"
        flat
        round
        dense
        :title="`Einstellungen ${name ?? ''}`"
        @click="settingsVisible = true"
      />
    </q-card-section>
    <q-separator class="q-mt-sm" />

    <q-card-section
      class="row q-mt-sm text-subtitle2 justify-between full-width"
    >
      <div>Leistung:</div>
      <div class="q-ml-sm">
        {{ power }}
      </div>
    </q-card-section>

    <q-card-section
      class="row q-mt-sm text-subtitle2 justify-between full-width"
    >
      <div>Laufzeit:</div>
      <div class="q-ml-sm">
        {{ runTime }}
      </div>
    </q-card-section>

    <q-card-section>
      <ConsumerMessage :consumer-id="props.consumerId" />
    </q-card-section>

    <template v-if="isOnOffType">
      <q-separator inset class="q-my-sm" />
      <q-card-section
        class="row items-center justify-between full-width text-subtitle2"
      >
        <div>Ein/Aus:</div>
        <ToggleStandard
          :value="onOff"
          size="md"
          @update:value="onOff = $event"
        />
      </q-card-section>
    </template>

    <ConsumerSettings
      :consumer-id="props.consumerId"
      v-model="settingsVisible"
    />
  </q-card>
</template>

<script setup lang="ts">
import { computed, ref } from 'vue';
import { useMqttStore } from 'src/stores/mqtt-store';
import ConsumerSettings from './ConsumerSettings.vue';
import ConsumerMessage from './ConsumerMessage.vue';
import ToggleStandard from './ToggleStandard.vue';

const props = defineProps<{
  consumerId: number;
  fullHeight?: boolean;
}>();

const mqttStore = useMqttStore();

const settingsVisible = ref(false);

const name = computed(() => mqttStore.consumerName(props.consumerId));

const power = computed(
  () => mqttStore.consumerPower(props.consumerId, 'textValue') as string,
);

const powerValue = computed(
  () => (mqttStore.consumerPower(props.consumerId, 'value') as number) || 0,
);
const isRunning = computed(() => powerValue.value > 0);

const runTime = computed<string>(() => {
  const seconds = mqttStore.consumerOnTime(props.consumerId);
  if (seconds === undefined) {
    return '--- h';
  }
  const totalMinutes = Math.floor(seconds / 60);
  const hours = Math.floor(totalMinutes / 60);
  const minutes = totalMinutes % 60;
  return `${hours}:${String(minutes).padStart(2, '0')} h`;
});

const faultState = computed(() => mqttStore.consumerFaultState(props.consumerId));

const statusText = computed(() => {
  if (faultState.value > 0) {
    return (
      mqttStore.consumerFaultStr(props.consumerId) ??
      mqttStore.consumerStateStr(props.consumerId)
    );
  }
  return mqttStore.consumerStateStr(props.consumerId);
});

const statusColor = computed(() => {
  if (faultState.value >= 2) {
    return 'negative';
  }
  if (faultState.value === 1) {
    return 'warning';
  }
  return isRunning.value ? 'positive' : 'grey-6';
});

const isOnOffType = computed(
  () => mqttStore.consumerUsageType(props.consumerId) === 'suspendable_onoff',
);

const consumerMode = mqttStore.consumerMode(props.consumerId);

// Toggle maps to Sofort (on) / Stop (off). Any non-stop mode reads as "on".
const onOff = computed({
  get: () => consumerMode.value !== undefined && consumerMode.value !== 'stop',
  set: (value: boolean) => {
    consumerMode.value = value ? 'instant_charging' : 'stop';
  },
});
</script>

<style scoped lang="scss">
.card-width {
  width: 100%;
  border: none;
  border-left: 4px solid var(--q-consumer);
  border-radius: 15px;
}

.q-card__section {
  padding-left: $space-base;
  padding-right: $space-base;
  padding-top: 0;
  padding-bottom: 0;
}

.q-card__section:first-of-type {
  padding-top: $space-base;
  padding-bottom: 0;
}

.q-card__section:last-of-type {
  padding-top: 0;
  padding-bottom: $space-base;
}

.q-card__section:not(:first-of-type):not(:last-of-type) {
  padding-top: 0;
  padding-bottom: 0;
}
</style>
